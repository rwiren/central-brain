import time
import json
import requests
import os
import logging
from datetime import datetime
from geopy.distance import geodesic
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

# ==========================================
# 1. CONFIGURATION & SETUP
# ==========================================

# --- DATA SOURCE (SDR) ---
# We pull JSON data from the local readsb container on the RPi5.
SDR_HOST = os.getenv('SDR_HOST', 'readsb')
SDR_PORT = os.getenv('SDR_PORT', '8080')
SDR_URL = f"http://{SDR_HOST}:{SDR_PORT}/data/aircraft.json"

# --- TARGET AIRPORT ---
TARGET_AIRPORT_CODE = os.getenv('TARGET_AIRPORT', 'EFHK')
# Center of Helsinki-Vantaa (EFHK)
AIRPORT_CENTER = (60.3172, 24.9633) 

# --- INFLUXDB CONNECTION ---
# Connects to the local database to store history.
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB = os.getenv('INFLUX_DB', 'readsb')
INFLUX_USER = os.getenv('INFLUX_USER', '')
INFLUX_PASS = os.getenv('INFLUX_PASS', '')

# --- MQTT CONNECTION ---
# Publishes real-time alerts to the broker for other services/UIs.
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = "aviation/events"

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("RunwayTracker")

# ==========================================
# 2. TUNING & CONSTANTS
# ==========================================

# DEBUG_MODE: If True, logic is very loose to catch ANY traffic near the airport.
# If False, requires strict runway alignment.
DEBUG_MODE = True 

# Search Radius: 
# 100km in Debug mode allows us to track planes on approach from Tallinn/Turku.
MONITOR_RADIUS_KM = 100 if DEBUG_MODE else 40

# EFHK Runway Definitions (Threshold coordinates)
RUNWAYS = {
    "04L": {"start": (60.3129, 24.9038), "heading": 46},
    "22R": {"start": (60.3311, 24.9438), "heading": 226},
    "04R": {"start": (60.3098, 24.9331), "heading": 46},
    "22L": {"start": (60.3306, 24.9790), "heading": 226},
    "15":  {"start": (60.3302, 24.9644), "heading": 151},
    "33":  {"start": (60.3070, 24.9882), "heading": 331}
}

# In-memory state to track aircraft across multiple poll cycles
flight_history = {}

# ==========================================
# 3. LOGIC FUNCTIONS
# ==========================================

def get_runway_alignment(lat, lon, track):
    """
    Determines if a plane is aligned with a runway.
    Returns: (Runway Name, Distance km) or (None, None)
    """
    for rwy, data in RUNWAYS.items():
        # 1. Heading Check: Is the plane pointing at the runway? (+/- 30 deg)
        diff = abs(track - data["heading"])
        if diff > 180: diff = 360 - diff
        if diff > 30: continue 

        # 2. Distance Check: Is it close to the threshold?
        dist = geodesic((lat, lon), data["start"]).km
        
        # In Debug mode, we allow detection up to 30km out.
        # In Strict mode, only 20km.
        limit = 30.0 if DEBUG_MODE else 20.0
        
        if dist < limit:
            return rwy, dist
            
    return None, None

def detect_phase(alt, v_rate, speed):
    """
    Classifies the flight phase based on physics data.
    """
    # GROUND: Very low and slow
    if alt < 500 and speed < 40: return "GROUND"
    
    # ROLLING: Low altitude, speed picking up, but not climbing fast yet
    if alt < 800 and speed >= 40 and v_rate < 400: return "ROLLING"
    
    # AIRBORNE PHASES
    if v_rate < -50: return "DESCENDING"
    if v_rate > 200: return "CLIMBING"
    
    return "LEVEL"

def main():
    logger.info(f"--- Runway Ops Tracker v3.0 ({TARGET_AIRPORT_CODE}) ---")
    logger.info(f"--- DEBUG MODE: {DEBUG_MODE} ---")

    # --------------------------------------
    # DATABASE CONNECTION LOOP
    # --------------------------------------
    client_influx = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, username=INFLUX_USER, password=INFLUX_PASS)
    while True:
        try:
            # Try to create DB if it doesn't exist
            client_influx.create_database(INFLUX_DB)
            client_influx.switch_database(INFLUX_DB)
            logger.info(f"✅ Connected to InfluxDB: {INFLUX_DB}")
            break
        except Exception as e:
            logger.warning(f"Waiting for InfluxDB... ({e})")
            time.sleep(5)

    # --------------------------------------
    # MQTT CONNECTION
    # --------------------------------------
    try:
        # Use VERSION2 callback API to avoid paho-mqtt 2.x crash
        client_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "RunwayTracker")
        client_mqtt.connect(MQTT_BROKER, MQTT_PORT)
        client_mqtt.loop_start()
        logger.info("✅ MQTT Connected")
        
        # Announce startup
        client_mqtt.publish(MQTT_TOPIC, json.dumps({"status": "online", "msg": "Tracker v3.0 Started", "debug": DEBUG_MODE}))
    except Exception as e:
        logger.error(f"MQTT Failed: {e}")
        client_mqtt = None

    # --------------------------------------
    # MAIN POLLING LOOP
    # --------------------------------------
    while True:
        try:
            # 1. Fetch Data from SDR
            try:
                r = requests.get(SDR_URL, timeout=2)
                if r.status_code != 200:
                    time.sleep(1)
                    continue
                    
                # Protect against empty response
                if not r.text.strip():
                    continue
                    
                data = r.json()
                aircraft = data.get('aircraft', [])
            except Exception as e:
                # Silent fail on fetch error to keep logs clean
                time.sleep(1)
                continue

            points = []

            # 2. Process Each Aircraft
            for ac in aircraft:
                # Validate Data
                icao = ac.get('hex')
                if not icao or 'lat' not in ac or 'lon' not in ac: continue
                
                # Filter by Distance (Global)
                dist_to_airport = geodesic((ac['lat'], ac['lon']), AIRPORT_CENTER).km
                if dist_to_airport > MONITOR_RADIUS_KM: 
                    # Clean up memory if plane flies away
                    if icao in flight_history: del flight_history[icao]
                    continue

                # Extract Physics
                alt = ac.get('alt_baro', 0)
                v_rate = ac.get('baro_rate', 0)
                speed = ac.get('gs', 0)
                track = ac.get('track', 0)
                callsign = ac.get('flight', 'N/A').strip()
                
                # Calculate State
                rwy, dist_to_rwy = get_runway_alignment(ac['lat'], ac['lon'], track)
                phase = detect_phase(alt, v_rate, speed)
                
                # Retrieve History
                history = flight_history.get(icao, {"state": "UNKNOWN", "logged": False})
                prev_state = history["state"]
                
                event_type = None
                event_rwy = rwy

                # --------------------------------------
                # SCENARIO A: LANDING DETECTION
                # --------------------------------------
                # Logic: Aligned with runway + Descending + Low Altitude
                landing_alt_limit = 10000 if DEBUG_MODE else 4000
                
                if rwy and phase == "DESCENDING" and alt < landing_alt_limit:
                    flight_history[icao]["state"] = "APPROACH"
                    
                    # Log Event (Once per approach)
                    if not history["logged"] and dist_to_rwy < 15.0:
                        event_type = "landing"
                        flight_history[icao]["logged"] = True
                        logger.info(f"🛬 LANDING: {callsign} on {rwy} (Alt: {alt}ft)")

                # --------------------------------------
                # SCENARIO B: TAKEOFF DETECTION
                # --------------------------------------
                # Logic 1 (Strict): Transition from Ground/Rolling -> Climbing
                elif (prev_state == "GROUND" or prev_state == "ROLLING") and phase == "CLIMBING" and rwy:
                     if not history["logged"]:
                        event_type = "takeoff"
                        flight_history[icao]["logged"] = True
                        flight_history[icao]["state"] = "CLIMBOUT"
                        logger.info(f"🛫 TAKEOFF: {callsign} from {rwy}")

                # Logic 2 (Debug/Loose): Just climbing near airport (missed ground phase)
                elif DEBUG_MODE and phase == "CLIMBING" and rwy and alt < 6000 and not history["logged"]:
                        event_type = "takeoff"
                        flight_history[icao]["logged"] = True
                        flight_history[icao]["state"] = "CLIMBOUT"
                        logger.info(f"🛫 TAKEOFF (Air Detected): {callsign} from {rwy}")

                # --------------------------------------
                # SCENARIO C: CATCH-ALL (NEARBY)
                # --------------------------------------
                # If DEBUG is on, log ANY descending plane near airport even if not aligned
                elif DEBUG_MODE and not rwy and dist_to_airport < 20.0 and phase == "DESCENDING" and not history["logged"]:
                    event_type = "landing"
                    event_rwy = "NEARBY" # Placeholder runway name
                    flight_history[icao]["logged"] = True
                    logger.info(f"🛬 NEARBY DESCENT: {callsign} (No runway match)")

                # --------------------------------------
                # STATE UPDATES
                # --------------------------------------
                elif phase == "ROLLING":
                     flight_history[icao] = {"state": "ROLLING", "rwy": rwy, "logged": history["logged"]}
                elif phase == "GROUND":
                    flight_history[icao] = {"state": "GROUND", "logged": False}

                # --------------------------------------
                # WRITE TO DB & MQTT
                # --------------------------------------
                if event_type:
                    # 1. InfluxDB Data Point
                    points.append({
                        "measurement": "runway_events",
                        "tags": {
                            "event": event_type, 
                            "runway": event_rwy, 
                            "callsign": callsign, 
                            "icao": icao
                        },
                        "fields": {
                            "altitude": float(alt), 
                            "speed": float(speed), 
                            "value": 1
                        }
                    })
                    
                    # 2. Update Active Runway Panel
                    if event_rwy != "NEARBY":
                        points.append({
                            "measurement": "airport_ops",
                            "tags": {"airport": TARGET_AIRPORT_CODE},
                            "fields": {"active_runway": event_rwy}
                        })

                    # 3. MQTT Publish
                    if client_mqtt:
                        payload = {
                            "event": event_type,
                            "runway": event_rwy,
                            "callsign": callsign,
                            "alt": alt,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        client_mqtt.publish(MQTT_TOPIC, json.dumps(payload))

            # Batch Write to DB
            if points:
                client_influx.write_points(points)

        except Exception as e:
            # General loop error catcher
            logger.error(f"Loop Error: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    main()
