import requests
import time
import os
from datetime import datetime
import json # Added to handle JSON response from token endpoint

# --- Configuration ---
# FIXED: InfluxDB runs on RPi5 (Central Server) at localhost
INFLUX_HOST = "http://127.0.0.1:8086"
INFLUX_DB = "readsb" 
INFLUX_WRITE_URL = f"{INFLUX_HOST}/write?db={INFLUX_DB}"

# OpenSky API configuration
# Using Client ID/Secret for OAuth2 authentication (required by OpenSky)
OPENSKY_CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID", None)
OPENSKY_CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET", None)
OPENSKY_AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

# Measurement name for global truth data
MEASUREMENT = "global_aircraft_state" 

# Time interval for fetching data (Respect OpenSky API limits)
FETCH_INTERVAL = 20 

# Global variable to hold the token and its expiration time (local to feeder)
auth_token_feeder = {
    "token": None,
    "expires_at": 0
}
TOKEN_LIFETIME = 300 # Token is typically valid for 300 seconds

# Bounding Box (BBOX) for your receiver's coverage area (Vantaa +/- 1 degree)
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
        print("[OpenSky] FATAL: Missing OPENSKY_CLIENT_ID/SECRET.")
        return None

    try:
        response = requests.post(
            OPENSKY_AUTH_URL,
            # Data format required by OAuth2 Client Credentials Flow
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
        auth_token_feeder["token"] = data.get("access_token")
        # Subtract 5 seconds to renew the token slightly before it expires
        auth_token_feeder["expires_at"] = time.time() + expires_in - 5 
        
        print(f"[OpenSky] Acquired new OAuth token. Expires in {expires_in}s.")
        return auth_token_feeder["token"]
        
    except requests.exceptions.RequestException as e:
        print(f"[OpenSky] CRITICAL: Failed to acquire token: {e}")
        return None


# ==========================================
# FETCH AND WRITE LOGIC
# ==========================================
def fetch_opensky_states():
    """Fetches real-time state vectors from OpenSky Network using Bearer token."""
    
    token = get_opensky_token_feeder()
    if not token:
        return []

    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    params = BBOX.copy() 
    
    try:
        response = requests.get(
            OPENSKY_API_URL,
            params=params,
            headers=headers,
            timeout=10
        )
        # 401/403 errors are now caught here; if so, force token refresh next cycle
        response.raise_for_status() 
        return response.json().get('states', [])
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401 or e.response.status_code == 403:
            print(f"[OpenSky] Sync error: Auth Token Rejected (401/403). Forcing token refresh.")
            auth_token_feeder["expires_at"] = 0 # Force token refresh
        else:
            print(f"[OpenSky] Sync error (HTTP {e.response.status_code}): {e}")
        return []
    
    except requests.exceptions.RequestException as e:
        print(f"[OpenSky] Sync error: {e}")
        return []


def format_state_to_line_protocol(state_vector):
    """
    Converts a single OpenSky state vector list into an InfluxDB Line Protocol string.
    """
    if not state_vector or len(state_vector) < 17:
        return None

    icao24 = state_vector[0]
    callsign = state_vector[1].strip() if state_vector[1] else "N/A"
    last_contact_time = state_vector[3] # time in Unix seconds
    
    latitude = state_vector[6]
    longitude = state_vector[5]
    baro_altitude = state_vector[7] # altitude in meters
    ground_speed = state_vector[9] # speed in m/s
    vertical_rate = state_vector[11] # vertical rate in m/s

    # InfluxDB Line Protocol: measurement,tags field=value timestamp
    
    # Tags (Indexed, good for filtering/grouping)
    tags = f"icao24={icao24},callsign={callsign}"

    # Fields (Values to be recorded)
    fields = [
        f"lat={latitude if latitude is not None else 0.0}",
        f"lon={longitude if longitude is not None else 0.0}",
        # Use floating point for derived values
        f"baro_alt_m={baro_altitude if baro_altitude is not None else 0.0}",
        f"gs_mps={ground_speed if ground_speed is not None else 0.0}",
        f"vr_mps={vertical_rate if vertical_rate is not None else 0.0}",
        # String fields require double quotes in InfluxDB 1.8 Line Protocol
        f'origin_data="OpenSky"' 
    ]
    
    # Timestamp (Using OpenSky time if available, otherwise current time)
    timestamp = int(last_contact_time * 1e9) if last_contact_time else int(time.time() * 1e9) 
    
    line = f"{MEASUREMENT},{tags} {','.join(fields)} {timestamp}"
    return line


def write_to_influxdb(line_data):
    """Sends the data line(s) to InfluxDB 1.8 using the HTTP API."""
    if not line_data:
        return
        
    try:
        response = requests.post(
            INFLUX_WRITE_URL, 
            data=line_data.encode('utf-8'), # Encode the line protocol string
            headers={'Content-Type': 'text/plain'},
            timeout=5
        )
        response.raise_for_status()
        # print(f"Successfully wrote {line_data.count('\\n') + 1} points to InfluxDB.")
        
    except requests.exceptions.HTTPError as err:
        print(f"InfluxDB HTTP Error: {err}. Response text: {err.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during InfluxDB write: {e}")


def main_loop():
    """Main loop for fetching and writing OpenSky data."""
    print(f"Starting OpenSky data feeder, targeting BBOX: {BBOX}")
    print(f"Writing to InfluxDB at: {INFLUX_WRITE_URL}")

    while True:
        start_time = time.time()
        
        # 1. Fetch States
        states = fetch_opensky_states()
        
        if states:
            # 2. Transform States to Line Protocol
            line_protocol_lines = []
            for state in states:
                line = format_state_to_line_protocol(state)
                if line:
                    line_protocol_lines.append(line)
            
            # 3. Write to InfluxDB
            if line_protocol_lines:
                write_data = "\n".join(line_protocol_lines)
                write_to_influxdb(write_data)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Wrote {len(line_protocol_lines)} OpenSky state vectors.")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetched {len(states)} states, but no valid data points found.")

        # 4. Wait for the next interval
        time_spent = time.time() - start_time
        wait_time = max(0, FETCH_INTERVAL - time_spent)
        time.sleep(wait_time)


if __name__ == "__main__":
    main_loop()
