import time
import threading
import json
import os
import requests
import math
import paho.mqtt.client as mqtt
from geopy.distance import geodesic
from datetime import datetime
from collections import deque

# ==========================================
# CONFIGURATION
# ==========================================

# 1. Environment Variables (Dynamic)
# We use the variables set in docker-compose
MY_LAT = float(os.getenv("MY_LAT", 60.3172))  # Vantaa default
MY_LON = float(os.getenv("MY_LON", 24.9633))

# 2. Data Sources
# We use the robust JSON API from the local container
LOCAL_READSB_URL = os.getenv("LOCAL_READSB_URL", "http://127.0.0.1:8080/data/aircraft.json")
OPENSKY_API_URL = "https://opensky-network.org/api/states/all"
OPENSKY_USER = os.getenv("OPENSKY_USER", None)
OPENSKY_PASS = os.getenv("OPENSKY_PASS", None)

# 3. MQTT Config (Optional)
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC_ALERTS = "aviation/alerts"

# 4. Helsinki Runway Headings (Approximate)
RUNWAYS = {
    "22L": (220, 230), "04R": (40, 50),
    "22R": (220, 230), "04L": (40, 50),
    "15":  (140, 160), "33":  (320, 340)
}

# 5. Global State
current_state = {
    "local": {},   # Data from RPi4 via Readsb
    "opensky": {}, # Data from OpenSky Network
    "history": {}  # For Go-Around detection
}
state_lock = threading.Lock()

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def identify_runway(lat, lon, heading, alt_ft):
    """Identifies if a plane is aligned with a known runway."""
    # Simple distance check to EFHK (Helsinki Vantaa)
    # 60.3172, 24.9633 is approx center
    plane_pos = (lat, lon)
    airport_pos = (60.3172, 24.9633) 
    
    try:
        dist_km = geodesic(plane_pos, airport_pos).km
        if dist_km < 10 and alt_ft < 3000:
            for rwy, (min_h, max_h) in RUNWAYS.items():
                if min_h <= heading <= max_h:
                    return rwy
    except:
        pass
    return "Unknown"

def send_alert(alert_type, details):
    """Sends alert via MQTT (if available) and prints to console."""
    msg = {
        "type": alert_type,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
    
    # 1. Print to Console (Always works)
    print(f"🚨 ALERT [{alert_type}]: {details}")
    
    # 2. Send to MQTT (If broker is alive)
    try:
        client.publish(MQTT_TOPIC_ALERTS, json.dumps(msg))
    except:
        pass # MQTT might be disabled, ignore error

# ==========================================
# MQTT SETUP
# ==========================================
client = mqtt.Client("SpoofDetector")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("[System] MQTT Connected")
except:
    print("[System] MQTT Disabled or Unreachable (Running in Console Mode)")

# ==========================================
# THREAD 1: LOCAL DATA POLLER (JSON)
# ==========================================
def local_poller_thread():
    """Reads aircraft.json from the local readsb web server."""
    while True:
        try:
            response = requests.get(LOCAL_READSB_URL, timeout=2)
            if response.status_code == 200:
                data = response.json()
                # Parse JSON into a clean dictionary
                new_data = {}
                for ac in data.get('aircraft', []):
                    if 'hex' in ac and 'lat' in ac and 'lon' in ac:
                        icao = ac['hex'].lower()
                        new_data[icao] = {
                            "hex": icao,
                            "flight": ac.get("flight", "N/A").strip(),
                            "lat": ac.get("lat"),
                            "lon": ac.get("lon"),
                            "alt": ac.get("alt_baro", 0), # feet
                            "speed": ac.get("gs", 0),     # knots
                            "track": ac.get("track", 0),
                            "v_rate": ac.get("baro_rate", 0), # fpm
                            "on_ground": ac.get("isOnGround", False) # json uses different key than csv
                        }
                
                with state_lock:
                    current_state["local"] = new_data
        except Exception as e:
            print(f"[Local] Error fetching data: {e}")
        
        time.sleep(1) # fast poll

# ==========================================
# THREAD 2: OPENSKY POLLER (TRUTH)
# ==========================================
def opensky_poller_thread():
    """Fetches truth data from OpenSky API (HTTP)."""
    while True:
        try:
            # 1 degree box around local position
            params = {
                "lamin": MY_LAT - 1.0,
                "lomin": MY_LON - 1.0,
                "lamax": MY_LAT + 1.0,
                "lomax": MY_LON + 1.0
            }
            
            auth = None
            if OPENSKY_USER and OPENSKY_PASS:
                auth = (OPENSKY_USER, OPENSKY_PASS)

            response = requests.get(OPENSKY_API_URL, params=params, auth=auth, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                new_data = {}
                if data and 'states' in data and data['states']:
                    for s in data['states']:
                        # s[0]=icao, s[5]=lon, s[6]=lat
                        if s[5] and s[6]:
                            new_data[s[0].lower()] = {
                                "lat": s[6],
                                "lon": s[5]
                            }
                
                with state_lock:
                    current_state["opensky"] = new_data
                print(f"[OpenSky] Synced {len(new_data)} aircraft.")
        except Exception as e:
            print(f"[OpenSky] Sync error: {e}")
        
        time.sleep(20) # Respect API limits

# ==========================================
# THREAD 3: ANALYZER (LOGIC)
# ==========================================
def analyzer_thread():
    """Compares streams and detects behaviors."""
    while True:
        time.sleep(2)
        
        with state_lock:
            local = current_state["local"].copy()
            truth = current_state["opensky"].copy()
            history = current_state["history"]

        for icao, ac in local.items():
            # --- 1. UPDATE HISTORY ---
            if icao not in history:
                history[icao] = deque(maxlen=5)
            
            history[icao].append({
                "alt": ac["alt"],
                "v_rate": ac["v_rate"],
                "speed": ac["speed"],
                "time": time.time()
            })
            
            # --- 2. LOGIC CHECKS ---
            if len(history[icao]) >= 2:
                prev = history[icao][-2]
                curr = history[icao][-1]

                # A. GO-AROUND DETECTION
                # Logic: Low altitude (<2000ft), was descending (-v_rate), now climbing fast (+v_rate)
                if curr['alt'] < 2000 and prev['v_rate'] < -200 and curr['v_rate'] > 500:
                    rwy = identify_runway(ac['lat'], ac['lon'], ac['track'], ac['alt'])
                    send_alert("GO-AROUND", f"{ac['flight']} at {rwy} (Alt: {ac['alt']}ft)")

                # B. SPOOF DETECTION
                # Logic: If OpenSky says plane is > 2km away from where we see it
                if icao in truth:
                    os_pos = (truth[icao]['lat'], truth[icao]['lon'])
                    my_pos = (ac['lat'], ac['lon'])
                    try:
                        dist = geodesic(my_pos, os_pos).km
                        if dist > 2.0:
                            send_alert("SPOOFING", f"{ac['flight']} Discrepancy: {dist:.1f}km")
                    except:
                        pass

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    print("--- WATCHDOG 2.0 STARTED ---")
    
    t1 = threading.Thread(target=local_poller_thread, daemon=True)
    t2 = threading.Thread(target=opensky_poller_thread, daemon=True)
    t3 = threading.Thread(target=analyzer_thread, daemon=True)
    
    t1.start()
    t2.start()
    t3.start()
    
    while True:
        time.sleep(1)
