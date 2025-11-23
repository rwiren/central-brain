import time
import json
import requests
import math
import os
import sys
from datetime import datetime
from geopy.distance import geodesic
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

# --- CONFIGURATION (Env Vars with Balena Defaults) ---
SDR_HOST = os.getenv('SDR_HOST', 'readsb')
SDR_PORT = os.getenv('SDR_PORT', '8080')
SDR_URL = f"http://{SDR_HOST}:{SDR_PORT}/data/aircraft.json"

# InfluxDB 1.8 Settings
INFLUX_HOST = os.getenv('INFLUX_HOST', 'influxdb')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB = os.getenv('INFLUX_DB', 'flight_ops')
# Leave user/pass empty if not configured in InfluxDB 1.8
INFLUX_USER = os.getenv('INFLUX_USER', '')
INFLUX_PASS = os.getenv('INFLUX_PASS', '')

# MQTT Settings
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = "adsb/events"

# EFHK Helsinki-Vantaa Precise Runway Thresholds
# "Start" is the landing threshold. "End" is the stop end.
RUNWAYS = {
    "04L": {
        "start": {"lat": 60.312947, "lon": 24.903869}, 
        "end":   {"lat": 60.331142, "lon": 24.943892}, 
        "heading": 46.3,
        "label": "Runway 04L (Main Landing)"
    },
    "22R": {
        "start": {"lat": 60.331142, "lon": 24.943892}, 
        "end":   {"lat": 60.312947, "lon": 24.903869}, 
        "heading": 226.3,
        "label": "Runway 22R (Main Takeoff)"
    },
    "04R": {
        "start": {"lat": 60.309839, "lon": 24.933175}, 
        "end":   {"lat": 60.330689, "lon": 24.979089}, 
        "heading": 46.3,
        "label": "Runway 04R"
    },
    "22L": {
        "start": {"lat": 60.330689, "lon": 24.979089}, 
        "end":   {"lat": 60.309839, "lon": 24.933175}, 
        "heading": 226.3,
        "label": "Runway 22L (Secondary Landing)"
    },
    "15": {
        "start": {"lat": 60.330275, "lon": 24.964497}, 
        "end":   {"lat": 60.307067, "lon": 24.988286}, 
        "heading": 151.3,
        "label": "Runway 15"
    },
    "33": {
        "start": {"lat": 60.307067, "lon": 24.988286}, 
        "end":   {"lat": 60.330275, "lon": 24.964497}, 
        "heading": 331.3,
        "label": "Runway 33"
    }
}

EFHK_CENTER = (60.3172, 24.9633)
MONITOR_RADIUS_KM = 30

def identify_runway(lat, lon, heading, altitude, vertical_rate):
    """
    Determines if aircraft is:
    1. Landing (Approaching 'Start' threshold, descending)
    2. Takeoff (Between 'Start' and 'End', climbing)
    """
    if altitude > 4000: return None, None # Ignore high altitude overflights

    best_rwy = None
    phase = None

    for rwy_id, data in RUNWAYS.items():
        # 1. Check Alignment (+/- 15 degrees)
        diff = abs(heading - data["heading"])
        if diff > 180: diff = 360 - diff
        if diff > 15: continue 

        # 2. Calculate distances
        dist_start = geodesic((lat, lon), (data["start"]["lat"], data["start"]["lon"])).km
        dist_end = geodesic((lat, lon), (data["end"]["lat"], data["end"]["lon"])).km

        # LOGIC A: LANDING
        # Within 10km of Start, Descending, and closer to Start than End
        if dist_start < 10.0 and dist_start < dist_end and vertical_rate < -100:
            if dist_start < 6.0: # High confidence zone
                return rwy_id, "Landing"

        # LOGIC B: TAKEOFF / ROLL
        # Between Start and End (on the runway) OR just past the End
        # Climbing or fast ground speed
        if dist_end < 6.0 and vertical_rate > 100:
             # If we are closer to the "End" of 22R than the "Start", we are likely taking off from it
             return rwy_id, "Takeoff"
    
    return None, None

def main():
    print("--- Starting EFHK Runway Ops Tracker ---")
    print(f"Connecting to InfluxDB: {INFLUX_HOST}:{INFLUX_PORT} (DB: {INFLUX_DB})")

    # 1. Connect to InfluxDB (Retry logic)
    while True:
        try:
            client_influx = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, username=INFLUX_USER, password=INFLUX_PASS)
            # Create DB if not exists
            current_dbs = client_influx.get_list_database()
            if not any(db['name'] == INFLUX_DB for db in current_dbs):
                print(f"Creating database {INFLUX_DB}...")
                client_influx.create_database(INFLUX_DB)
            client_influx.switch_database(INFLUX_DB)
            print("InfluxDB Connected!")
            break
        except Exception as e:
            print(f"InfluxDB Connection failed: {e}. Retrying in 5s...")
            time.sleep(5)

    # 2. Connect to MQTT (Optional but recommended)
    client_mqtt = mqtt.Client(client_id="efhk_tracker_service")
    try:
        client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        client_mqtt.loop_start()
        print("MQTT Connected!")
    except Exception as e:
        print(f"MQTT Warning (running without): {e}")

    # 3. Main Processing Loop
    while True:
        try:
            r = requests.get(SDR_URL, timeout=2)
            if r.status_code != 200:
                print(f"SDR Error: Status {r.status_code}")
                time.sleep(5)
                continue

            data = r.json()
            points = []
            # Use UTC time formatted for InfluxDB
            now_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

            for ac in data.get('aircraft', []):
                # Basic data validation
                if not all(k in ac for k in ['lat', 'lon', 'track', 'alt_baro', 'hex']):
                    continue

                # Distance Filter
                if geodesic((ac['lat'], ac['lon']), EFHK_CENTER).km > MONITOR_RADIUS_KM:
                    continue

                # Run Logic
                rwy, phase = identify_runway(
                    ac['lat'], ac['lon'], ac['track'], 
                    ac['alt_baro'], ac.get('baro_rate', 0)
                )

                if rwy:
                    # Prepare Influx Point
                    point = {
                        "measurement": "runway_ops",
                        "tags": {
                            "icao": ac['hex'],
                            "callsign": ac.get('flight', 'N/A').strip(),
                            "runway": rwy,
                            "phase": phase
                        },
                        "time": now_str,
                        "fields": {
                            "alt": float(ac['alt_baro']),
                            "lat": float(ac['lat']),
                            "lon": float(ac['lon']),
                            "heading": float(ac['track']),
                            "v_rate": float(ac.get('baro_rate', 0)),
                            "count": 1
                        }
                    }
                    points.append(point)

                    # MQTT Alert (JSON)
                    alert = {
                        "icao": ac['hex'],
                        "flight": ac.get('flight', 'N/A').strip(),
                        "msg": f"{phase} {rwy}",
                        "ts": now_str
                    }
                    client_mqtt.publish(f"{MQTT_TOPIC}/{ac['hex']}", json.dumps(alert))
                    
                    # Log to console for debugging
                    print(f"[EVENT] {alert['flight']} -> {phase} {rwy} (Alt: {ac['alt_baro']})")

            # Batch write to InfluxDB
            if points:
                client_influx.write_points(points)

        except requests.exceptions.ConnectionError:
            print("Waiting for readsb container...")
            time.sleep(5)
        except Exception as e:
            print(f"Error in loop: {e}")
            time.sleep(1)
        
        time.sleep(1.0) # Poll frequency

if __name__ == "__main__":
    main()
