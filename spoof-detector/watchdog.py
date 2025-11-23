import time
import threading
import json
import os
import requests
import math
from geopy.distance import geodesic
from datetime import datetime
from collections import deque
import paho.mqtt.client as mqtt

# ==========================================
# CONFIGURATION
# ==========================================

# 1. Environment Variables (Dynamic)
# MY_LAT/MY_LON are read from Balena environment variables ($LAT/$LON)
MY_LAT = float(os.getenv("MY_LAT", 60.3172))  # Vantaa default
MY_LON = float(os.getenv("LON", 24.9633))

# 2. Data Sources
# FIXED: Targets RPi4's actual IP address for JSON source (solves 404 errors)
LOCAL_READSB_URL = "http://192.168.1.152:8080/data/aircraft.json"
OPENSKY_API_URL = "https://opensky-network.org/api/states/all"
# FIXED: Using Client ID/Secret for real-time watchdog auth
OPENSKY_CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID", None)
OPENSKY_CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET", None)
OPENSKY_AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

# 3. MQTT Config (Optional)
# 127.0.0.1 is correct for host network mode
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
    "local": {},  # Data from RPi4 via Readsb
    "opensky": {}, # Data from OpenSky Network
    "history": {}  # For Go-Around detection
}
state_lock = threading.Lock()

# Global variable to hold the token and its expiration time (local to watchdog)
auth_token_watchdog = {
    "token": None,
    "expires_at": 0
}
TOKEN_LIFETIME = 300 # Token is typically valid for 300 seconds

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def identify_runway(lat, lon, heading, alt_ft):
    """Identifies if a plane is aligned with a known runway."""
    plane_pos = (lat, lon)
    airport_pos = (60.3172, 24.9633)
    
    try:
        dist_km = geodesic(plane_pos, airport_pos).km
        if dist_km < 10 and alt_ft < 3000:
            for rwy, (min_h, max_h) in RUNWAYS.items():
                # Correctly check if heading falls within the runway band
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
# OPENSKY OAUTH HANDLER (Internal to Watchdog)
# ==========================================
def get_opensky_token_watchdog():
    """Requests a new OAuth2 Bearer Token for the watchdog."""
    global auth_token_watchdog

    # Check if current token is still valid
    if auth_token_watchdog["token"] and time.time() < auth_token_watchdog["expires_at"]:
        return auth_token_watchdog["token"]

    if not OPENSKY_CLIENT_ID or not OPENSKY_CLIENT_SECRET:
        print("[OpenSky] FATAL: Missing OPENSKY_CLIENT_ID/SECRET for watchdog.")
        return None

    try:
        response = requests.post(
            OPENSKY_AUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": OPENSKY_CLIENT_ID,
                "client_secret": OPENSKY_CLIENT_SECRET
            },
            timeout=5
        )
        response.raise_for_status() # Raise exception for 4xx/5xx errors
        data = response.json()
        
        expires_in = data.get("expires_in", TOKEN_LIFETIME)
        auth_token_watchdog["token"] = data.get("access_token")
        # Subtract 5 seconds to renew the token slightly before it expires
        auth_token_watchdog["expires_at"] = time.time() + expires_in - 5 
        
        print(f"[OpenSky] Acquired new OAuth token for watchdog. Expires in {expires_in}s.")
        return auth_token_watchdog["token"]
        
    except requests.exceptions.RequestException as e:
        print(f"[OpenSky] CRITICAL: Failed to acquire watchdog token: {e}")
        return None

# ==========================================
# THREAD 1: LOCAL DATA POLLER (JSON)
# ==========================================
def local_poller_thread():
    """Reads aircraft.json from the RPi4 web server."""
    while True:
        try:
            # Targets RPi4 directly
            response = requests.get(LOCAL_READSB_URL, timeout=2)
            response.raise_for_status() # Raise error on 4xx/5xx responses
            
            data = response.json()
            # Parse JSON into a clean dictionary
            new_data = {}
            for ac in data.get('aircraft', []):
                # Only process aircraft with required hex, lat, and lon
                if 'hex' in ac and 'lat' in ac and 'lon' in ac:
                    # Handle the 'alt_baro' value which can be a string ("ground")
                    alt_value = ac.get('alt_baro', 0)
                    if isinstance(alt_value, str):
                        alt_ft = 0 # Default altitude to 0 if on ground
                        v_rate = 0 # Default vertical rate to 0
                    else:
                        alt_ft = alt_value
                        v_rate = ac.get("baro_rate", 0) # fpm
                        
                    icao = ac['hex'].lower()
                    new_data[icao] = {
                        "hex": icao,
                        "flight": ac.get("flight", "N/A").strip(),
                        "lat": ac.get("lat"),
                        "lon": ac.get("lon"),
                        "alt": alt_ft,                # feet (0 if on ground)
                        "speed": ac.get("gs", 0),     # knots
                        "track": ac.get("track", 0),
                        "v_rate": v_rate,             # fpm (0 if on ground)
                        "on_ground": alt_ft == 0 and ac.get("gs", 0) < 50 # Heuristic check
                    }
            
            with state_lock:
                current_state["local"] = new_data
            
            time.sleep(1.5) 
            
        except requests.exceptions.HTTPError as err:
            # Check if the service is running, otherwise log the error
            print(f"[Local] Error fetching data (HTTP {err.response.status_code}): {LOCAL_READSB_URL}")
            time.sleep(5)
        except Exception as e:
            print(f"[Local] Error fetching data: {e}")
            time.sleep(5)

# ==========================================
# THREAD 2: OPENSKY POLLER (TRUTH)
# ==========================================
def opensky_poller_thread():
    """Fetches truth data from OpenSky API (HTTP)."""
    while True:
        try:
            token = get_opensky_token_watchdog()
            if not token:
                time.sleep(20)
                continue

            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # Use centralized location for the BBOX
            params = {
                "lamin": MY_LAT - 1.0,
                "lomin": MY_LON - 1.0,
                "lamax": MY_LAT + 1.0,
                "lomax": MY_LON + 1.0
            }
            
            response = requests.get(OPENSKY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status() # Raises the 401 Client Error if unauthorized
            
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
            
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 401 or err.response.status_code == 403:
                 print(f"[OpenSky] Sync error: Authentication Failed (401/403). Check Client ID/Secret or permissions.")
                 # Force token refresh next cycle
                 auth_token_watchdog["expires_at"] = 0 
            else:
                 print(f"[OpenSky] Sync error (HTTP {err.response.status_code}): {err}")
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
