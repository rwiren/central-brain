import requests
import time
import os
import re
import sys
from datetime import datetime

# ==============================================================================
# Script: opensky_feeder.py
# Service: Global Truth Data (OpenSky Network)
# Version: 6.0.0 (AI Schema Alignment)
# Description: 
#   Fetches Global Reference data using OAuth2.
#   Aligns schema EXACTLY with local_aircraft_state for AI comparison.
# ==============================================================================

# --- CONFIGURATION ---
INFLUX_HOST = os.getenv("INFLUX_HOST", "http://influxdb:8086")
INFLUX_DB = os.getenv("INFLUX_DB", "readsb")
INFLUX_WRITE_URL = f"{INFLUX_HOST}/write?db={INFLUX_DB}"

# OAuth2 Credentials
CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")

# Endpoints
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
API_URL = "https://opensky-network.org/api/states/all"

# Location (Dynamic Bounding Box)
try:
    CENTER_LAT = float(os.getenv("MY_LAT") or os.getenv("LAT") or 60.319555)
    CENTER_LON = float(os.getenv("MY_LON") or os.getenv("LON") or 24.830819)
except ValueError:
    CENTER_LAT, CENTER_LON = 60.3196, 24.8308

# Bounding Box (~1.5 degree box for broader "Truth" horizon)
BBOX_PARAMS = {
    'lamin': CENTER_LAT - 0.75,
    'lomin': CENTER_LON - 1.5,
    'lamax': CENTER_LAT + 0.75,
    'lomax': CENTER_LON + 1.5
}

# Token Storage
AUTH_SESSION = {
    "token": None,
    "expires_at": 0
}

def clean_tag(value):
    """Removes spaces/special chars to prevent Line Protocol breakage."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', str(value).strip())

def get_token():
    """Exchanges Client ID/Secret for a Bearer Token."""
    # Return valid cached token
    if AUTH_SESSION["token"] and time.time() < AUTH_SESSION["expires_at"]:
        return AUTH_SESSION["token"]

    print("[OpenSky] Requesting new OAuth2 Token...")
    try:
        payload = {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        r = requests.post(TOKEN_URL, data=payload, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            token = data.get('access_token')
            expires_in = data.get('expires_in', 300)
            
            AUTH_SESSION["token"] = token
            AUTH_SESSION["expires_at"] = time.time() + expires_in - 30 # Buffer
            
            print(f"[OpenSky] Token acquired. Expires in {expires_in}s.")
            return token
        else:
            print(f"[OpenSky] Auth Failed: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"[OpenSky] Auth Error: {e}")
        return None

def main():
    print(f"--- OpenSky Feeder v6.0.0 (AI Schema) ---")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ CRITICAL: OPENSKY_CLIENT_ID or OPENSKY_CLIENT_SECRET missing.")
        print("   Running in Anonymous Mode (Very limited rate/data).")
    
    while True:
        try:
            # 1. Get Token
            token = get_token() if CLIENT_ID else None
            
            # 2. Prepare Headers
            headers = {}
            if token:
                headers['Authorization'] = f"Bearer {token}"
            
            # 3. Fetch Data
            start_t = time.time()
            r = requests.get(API_URL, params=BBOX_PARAMS, headers=headers, timeout=15)
            
            if r.status_code == 200:
                data = r.json()
                states = data.get('states', [])
                
                if states:
                    lines = []
                    now_ns = int(time.time() * 1e9)
                    
                    for s in states:
                        # Vector Index Reference:
                        # 0:icao24, 1:callsign, 2:country, 3:time, 4:last_contact
                        # 5:lon, 6:lat, 7:baro_alt, 8:on_ground
                        # 9:velocity, 10:true_track, 11:vert_rate
                        # 13:geo_alt, 14:squawk, 15:spi, 16:pos_source

                        if s[5] is None or s[6] is None: continue 

                        # --- TAGS (Indexed) ---
                        icao = clean_tag(s[0])
                        call = clean_tag(s[1] or "N/A")
                        country = clean_tag(s[2] or "Unknown")
                        
                        tags = f"icao24={icao},callsign={call},origin_country={country},source=OpenSkyNetwork"
                        
                        # --- FIELDS (Data) ---
                        # We explicitly map these to match 'local_aircraft_state' fields
                        
                        # Physics
                        lat = float(s[6])
                        lon = float(s[5])
                        alt_baro = int(s[7] * 3.28084) if s[7] is not None else 0
                        alt_geom = int(s[13] * 3.28084) if s[13] is not None else 0
                        gs = float(s[9] * 1.94384) if s[9] is not None else 0.0
                        track = float(s[10]) if s[10] is not None else 0.0
                        vert_rate = int(s[11] * 196.85) if s[11] is not None else 0
                        
                        # Status
                        squawk = str(s[14] if s[14] else "None")
                        on_ground = str(s[8]).lower()
                        
                        fields = [
                            f"lat={lat}",
                            f"lon={lon}",
                            f"alt_baro_ft={alt_baro}i",
                            f"alt_geom_ft={alt_geom}i",
                            f"gs_knots={gs}",
                            f"track={track}",
                            f"vert_rate_fpm={vert_rate}i",
                            f'squawk="{squawk}"',
                            f'on_ground="{on_ground}"',
                            
                            # Dummy fields for schema compatibility with Local Data
                            f"rssi=-1.0", 
                            f'origin_data="GlobalReference"'
                        ]
                        
                        lines.append(f"global_aircraft_state,{tags} {','.join(fields)} {now_ns}")

                    # Write to Influx
                    if lines:
                        w = requests.post(INFLUX_WRITE_URL, data="\n".join(lines), timeout=5)
                        if w.status_code < 400:
                            print(f"[OpenSky] Pushed {len(lines)} aircraft (Global Truth).")
                        else:
                            print(f"[OpenSky] DB Write Error: {w.status_code}")
                else:
                    print(f"[OpenSky] Area Empty.")

            elif r.status_code == 401:
                print("[OpenSky] 401 Unauthorized. Refreshing token...")
                AUTH_SESSION["token"] = None 
                time.sleep(1)
                continue

            elif r.status_code == 429:
                print("[OpenSky] Rate Limit Hit. Sleeping 60s.")
                time.sleep(60)
            
            else:
                print(f"[OpenSky] API Error: {r.status_code}")

        except Exception as e:
            print(f"[OpenSky] Loop Error: {e}")

        # Poll Interval (10s for Auth, 30s for Anon)
        time.sleep(15 if CLIENT_ID else 30)

if __name__ == "__main__":
    main()
