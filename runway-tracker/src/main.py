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
# 1. CONFIGURATION
# ==========================================

# SDR / Data Source
SDR_HOST = os.getenv('SDR_HOST', 'readsb')
SDR_PORT = os.getenv('SDR_PORT', '8080')
SDR_URL = f"http://{SDR_HOST}:{SDR_PORT}/data/aircraft.json"

# Central Brain Assets (The Gazetteer)
# Defaults to the internal docker DNS for the grafana container
GAZETTEER_URL = os.getenv('GAZETTEER_URL', 'http://grafana:3000/public/gazetteer/airports.geojson')
TARGET_AIRPORT_CODE = os.getenv('TARGET_AIRPORT', 'EFHK')

# InfluxDB Settings (Forcing 'readsb' based on your logs)
INFLUX_HOST = os.getenv('INFLUX_HOST', 'influxdb')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB = os.getenv('INFLUX_DB', 'readsb') 
INFLUX_USER = os.getenv('INFLUX_USER', '')
INFLUX_PASS = os.getenv('INFLUX_PASS', '')

# MQTT Settings
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = "aviation/events"

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("RunwayTracker")

# ==========================================
# 2. AIRPORT & PHYSICS CONSTANTS
# ==========================================

# Default Center (Will be overwritten by Gazetteer if available)
AIRPORT_CENTER = (60.3172, 24.9633) # EFHK

# [TUNING] How far out to track planes?
# 40km allows catching the glide slope early.
MONITOR_RADIUS_KM = 40 

# Precise Runway Thresholds (EFHK)
# Start = Threshold, End = Stop End, Heading = Magnetic
RUNWAYS = {
    "04L": {"start": (60.3129, 24.9038), "end": (60.3311, 24.9438), "heading": 46},
    "22R": {"start": (60.3311, 24.9438), "end": (60.3129, 24.9038), "heading": 226},
    "04R": {"start": (60.3098, 24.9331), "end": (60.3306, 24.9790), "heading": 46},
    "22L": {"start": (60.3306, 24.9790), "end": (60.3098, 24.9331), "heading": 226},
    "15":  {"start": (60.3302, 24.9644), "end": (60.3070, 24.9882), "heading": 151},
    "33":  {"start": (60.3070, 24.9882), "end": (60.3302, 24.9644), "heading": 331}
}

# Flight History Memory
flight_history = {} 

# ==========================================
# 3. LOGIC FUNCTIONS
# ==========================================

def fetch_airport_metadata():
    """Auto-configures airport location from local gazetteer."""
    global AIRPORT_CENTER
    logger.info(f"Fetching metadata for {TARGET_AIRPORT_CODE}...")
    try:
        r = requests.get(GAZETTEER_URL, timeout=5)
        if r.status_code == 200:
            data = r.json()
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                if props.get('gps_code') == TARGET_AIRPORT_CODE:
                    # GeoJSON is [Lon, Lat], Geopy needs (Lat, Lon)
                    coords = feature['geometry']['coordinates']
                    AIRPORT_CENTER = (coords[1], coords[0])
                    logger.info(f"✅ Locked on {props['name']} at {AIRPORT_CENTER}")
                    return
    except Exception as e:
        logger.warning(f"Gazetteer skipped: {e}")

def get_runway_alignment(lat, lon, track):
    """Checks if aircraft is aligned with any runway."""
    for rwy, data in RUNWAYS.items():
        # [TUNING] Heading Tolerance (+/- degrees)
        # 25 deg accounts for crab angle during crosswind landings
        diff = abs(track - data["heading"])
        if diff > 180: diff = 360 - diff
        if diff > 25: continue 

        # [TUNING] Distance from Threshold (km)
        # 25km captures the "Established on Localizer" phase.
        dist = geodesic((lat, lon), data["start"]).km
        if dist < 25.0:
            return rwy, dist
    return None, None

def detect_phase(alt, v_rate, speed):
    """
    Classifies flight phase based on physics.
    """
    # [TUNING] Ground Logic
    # Speed < 40kts AND Alt < 500ft (AGL approx) = Taxiing
    if alt < 500 and speed < 40: 
        return "GROUND"
    
    # [TUNING] Takeoff Roll Logic
    # Speed > 40kts BUT Vertical Rate is low (< 400fpm) = Rolling for Takeoff
    # This detects the acceleration phase before lift-off
    if alt < 800 and speed >= 40 and v_rate < 400:
        return "ROLLING"

    # [TUNING] Descent Logic
    # Any negative vertical rate or holding level while aligned
    if v_rate < -50: 
        return "DESCENDING"
        
    # [TUNING] Climb Logic
    # Positive rate > 200fpm means they are airborne
    if v_rate > 200: 
        return "CLIMBING"
        
    return "LEVEL"

def main():
    print(f"--- Runway Ops Tracker v2.3 ({TARGET_AIRPORT_CODE}) ---")
    fetch_airport_metadata()
    
    # --- DB Setup ---
    client_influx = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, username=INFLUX_USER, password=INFLUX_PASS)
    while True:
        try:
            dbs = client_influx.get_list_database()
            if not any(d['name'] == INFLUX_DB for d in dbs):
                client_influx.create_database(INFLUX_DB)
            client_influx.switch_database(INFLUX_DB)
            print(f"Connected to InfluxDB: {INFLUX_DB}")
            break
        except:
            print("Waiting for InfluxDB...")
            time.sleep(5)

    # --- MQTT Setup (CRASH FIX) ---
    # We explicitly use CallbackAPIVersion.VERSION2 to support paho-mqtt 2.0.0+
    try:
        client_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "RunwayTracker")
        client_mqtt.connect(MQTT_BROKER, MQTT_PORT)
        client_mqtt.loop_start()
        print("MQTT Connected")
    except Exception as e:
        print(f"MQTT Failed ({e}) - Running offline mode")
        client_mqtt = None

    # --- Main Loop ---
    while True:
        try:
            r = requests.get(SDR_URL, timeout=2)
            if r.status_code != 200: 
                time.sleep(1)
                continue
            
            aircraft = r.json().get('aircraft', [])
            current_time = time.time()
            points = []

            for ac in aircraft:
                icao = ac.get('hex')
                # Skip if missing critical data
                if not icao or 'lat' not in ac or 'track' not in ac: continue

                # Distance Filter (Global)
                if geodesic((ac['lat'], ac['lon']), AIRPORT_CENTER).km > MONITOR_RADIUS_KM:
                    if icao in flight_history: del flight_history[icao]
                    continue

                # Physics Extraction
                alt = ac.get('alt_baro', 0)
                v_rate = ac.get('baro_rate', 0)
                speed = ac.get('gs', 0)
                track = ac.get('track', 0)
                callsign = ac.get('flight', 'N/A').strip()

                # Analysis
                rwy, dist = get_runway_alignment(ac['lat'], ac['lon'], track)
                phase = detect_phase(alt, v_rate, speed)
                
                # State Machine
                history = flight_history.get(icao, {"state": "UNKNOWN", "logged": False})
                prev_state = history["state"]
                event_type = None
                
                # 1. DETECT LANDING (Loosened Logic)
                # Detects up to 4000ft altitude and 12km out
                if rwy and phase == "DESCENDING" and alt < 4000:
                    flight_history[icao] = {
                        "state": "APPROACH", 
                        "rwy": rwy, 
                        "logged": history["logged"]
                    }
                    
                    # Log event if we haven't already for this approach
                    if not history["logged"] and dist < 12.0:
                        event_type = "landing"
                        flight_history[icao]["logged"] = True
                        logger.info(f"🛬 LANDING: {callsign} on {rwy} (Alt: {alt}ft)")

                # 2. DETECT TAKEOFF
                # If previously GROUND or ROLLING, and now CLIMBING
                elif (prev_state == "GROUND" or prev_state == "ROLLING") and phase == "CLIMBING" and rwy:
                     if not history.get("logged", False):
                        event_type = "takeoff"
                        flight_history[icao]["logged"] = True
                        flight_history[icao]["state"] = "CLIMBOUT"
                        logger.info(f"🛫 TAKEOFF: {callsign} on {rwy} (Spd: {speed}kts)")
                
                # 3. TRACKING THE ROLL
                elif phase == "ROLLING":
                     flight_history[icao] = {"state": "ROLLING", "rwy": rwy, "logged": history["logged"]}
                
                # 4. DETECT GO-AROUND
                elif prev_state == "APPROACH" and phase == "CLIMBING" and alt < 3500 and rwy:
                    if history.get("rwy") == rwy:
                        event_type = "go_around"
                        logger.warning(f"🚨 GO AROUND: {callsign} on {rwy}")
                        flight_history[icao]["state"] = "CLIMBOUT"

                # Reset State on Ground
                if phase == "GROUND":
                    flight_history[icao] = {"state": "GROUND", "logged": False}

                # Write to InfluxDB
                if event_type:
                    points.append({
                        "measurement": "runway_events",
                        "tags": {
                            "event": event_type,
                            "runway": rwy,
                            "callsign": callsign,
                            "icao": icao
                        },
                        "fields": {
                            "altitude": float(alt),
                            "speed": float(speed),
                            "value": 1
                        }
                    })
                    
                    # Update Active Runway State
                    points.append({
                        "measurement": "airport_ops",
                        "tags": {"airport": TARGET_AIRPORT_CODE},
                        "fields": {"active_runway": rwy}
                    })

            if points:
                client_influx.write_points(points)

        except Exception as e:
            logger.error(f"Loop Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    main()
