import requests
import time
import os
from datetime import datetime
import json

# --- Configuration ---
# FIXED: InfluxDB runs on RPi5 (Central Server) at localhost
INFLUX_HOST = os.getenv("INFLUX_HOST", "http://127.0.0.1:8086")
INFLUX_DB = os.getenv("INFLUX_DB", "readsb")
INFLUX_WRITE_URL = f"{INFLUX_HOST}/write?db={INFLUX_DB}"

# OpenSky API configuration
# Using Client ID/Secret for OAuth2 authentication
OPENSKY_CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID", None)
OPENSKY_CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET", None)
OPENSKY_AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

# Measurement name for global truth data
MEASUREMENT = "global_aircraft_state"

# Time interval for fetching data (Respect OpenSky API limits)
# 10s for Authenticated, 20s+ for Anonymous
FETCH_INTERVAL = 30 

# Global variable to hold the token and its expiration time
auth_token_feeder = {
    "token": None,
    "expires_at": 0
}
TOKEN_LIFETIME = 300 

# Bounding Box (BBOX)
MY_LAT = float(os.getenv("LAT", 60.320863)) 
MY_LON = float(os.getenv("LON", 24.84125)) 
BBOX = {
    'lamin': MY_LAT - 1.0, 
    'lomin': MY_LON - 1.0,
    'lamax': MY_LAT + 1.0, 
    'lomax': MY_LON + 1.0
}

# ==========================================
# OPENSKY OAUTH HANDLER
# ==========================================
def get_opensky_token_feeder():
    """Requests a new OAuth2 Bearer Token for the data feeder."""
    global auth_token_feeder

    # Check if current token is still valid
    if auth_token_feeder["token"] and time.time() < auth_token_feeder["expires_at"]:
        return auth_token_feeder["token"]

    if not OPENSKY_CLIENT_ID or not OPENSKY_CLIENT_SECRET:
        # If no credentials, return None to use Anonymous mode (limited quota)
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
        response.raise_for_status()
        data = response.json()
        
        expires_in = data.get("expires_in", TOKEN_LIFETIME)
        auth_token_feeder["token"] = data.get("access_token")
        auth_token_feeder["expires_at"] = time.time() + expires_in - 5 
        
        print(f"[OpenSky] Acquired new OAuth token. Expires in {expires_in}s.")
        return auth_token_feeder["token"]
        
    except requests.exceptions.RequestException as e:
        print(f"[OpenSky] Auth Failed (Using Anonymous Mode): {e}")
        return None


# ==========================================
# FETCH AND WRITE LOGIC
# ==========================================
def fetch_opensky_states():
    """Fetches real-time state vectors from OpenSky Network."""
    
    token = get_opensky_token_feeder()
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    params = BBOX.copy() 
    
    try:
        response = requests.get(
            OPENSKY_API_URL,
            params=params,
            headers=headers,
            timeout=10
        )
        
        # --- FIX: Specific Handling for 429 (Rate Limit) ---
        if response.status_code == 429:
            print("[OpenSky] RATE LIMIT HIT (429). Cooling down for 60s...")
            time.sleep(60) # Penalty wait
            return []

        response.raise_for_status() 
        return response.json().get('states', [])
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403]:
            print(f"[OpenSky] Auth Token Expired/Rejected. Forcing refresh.")
            auth_token_feeder["expires_at"] = 0 
        else:
            print(f"[OpenSky] HTTP Error {e.response.status_code}: {e}")
        return []
    
    except requests.exceptions.RequestException as e:
        print(f"[OpenSky] Connection Error: {e}")
        return []


def format_state_to_line_protocol(state_vector):
    """Converts a single OpenSky state vector list into InfluxDB Line Protocol."""
    if not state_vector or len(state_vector) < 17:
        return None

    icao24 = state_vector[0]
    callsign = state_vector[1].strip() if state_vector[1] else "N/A"
    last_contact_time = state_vector[3] 
    
    latitude = state_vector[6]
    longitude = state_vector[5]
    baro_altitude = state_vector[7] 
    ground_speed = state_vector[9] 
    vertical_rate = state_vector[11] 

    tags = f"icao24={icao24},callsign={callsign}"

    fields = [
        f"lat={latitude if latitude is not None else 0.0}",
        f"lon={longitude if longitude is not None else 0.0}",
        f"baro_alt_m={baro_altitude if baro_altitude is not None else 0.0}",
        f"gs_mps={ground_speed if ground_speed is not None else 0.0}",
        f"vr_mps={vertical_rate if vertical_rate is not None else 0.0}",
        f'origin_data="OpenSky"' 
    ]
    
    timestamp = int(last_contact_time * 1e9) if last_contact_time else int(time.time() * 1e9) 
    
    line = f"{MEASUREMENT},{tags} {','.join(fields)} {timestamp}"
    return line


def write_to_influxdb(line_data):
    """Sends the data line(s) to InfluxDB."""
    if not line_data:
        return
        
    try:
        response = requests.post(
            INFLUX_WRITE_URL, 
            data=line_data.encode('utf-8'),
            headers={'Content-Type': 'text/plain'},
            timeout=5
        )
        if response.status_code not in [200, 204]:
             print(f"InfluxDB Write Failed: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"InfluxDB Connection Error: {e}")


def main_loop():
    print(f"Starting OpenSky Feeder...")
    print(f"Target: {INFLUX_WRITE_URL}")
    print(f"BBOX: {BBOX}")

    while True:
        start_time = time.time()
        
        states = fetch_opensky_states()
        
        if states:
            lines = []
            for state in states:
                line = format_state_to_line_protocol(state)
                if line:
                    lines.append(line)
            
            if lines:
                write_data = "\n".join(lines)
                write_to_influxdb(write_data)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Wrote {len(lines)} vectors from OpenSky.")
        
        # Wait for next interval
        time_spent = time.time() - start_time
        wait_time = max(0, FETCH_INTERVAL - time_spent)
        time.sleep(wait_time)


if __name__ == "__main__":
    main_loop()
