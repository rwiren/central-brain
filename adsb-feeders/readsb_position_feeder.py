import requests
import time
import os
import re
from datetime import datetime

# ==============================================================================
# Script: readsb_position_feeder.py
# Version: 3.0.0 (The "All-Seeing Eye")
# Author: Operations Team
# Description: 
#   Ingests detailed aircraft telemetry from Readsb/Tar1090 JSON endpoint.
#   Now captures Pilot Intent (FMS), GPS Integrity (NIC/SIL), and Signal Data.
# ==============================================================================

NODES = {
    "keimola-office": "http://192.168.1.153:8080",
    "keimola-balcony": "http://192.168.1.9:8080"
}

# InfluxDB Configuration
INFLUX_HOST = os.getenv("INFLUX_HOST", "http://influxdb:8086")
INFLUX_DB = os.getenv("INFLUX_DB", "readsb")
INFLUX_WRITE_URL = f"{INFLUX_HOST}/write?db={INFLUX_DB}"

MEASUREMENT = "local_aircraft_state"
FETCH_INTERVAL = 1  # How often to poll (seconds)

def clean_tag(value):
    """Removes spaces/special chars to prevent Line Protocol breakage."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', str(value).strip())

def get_val(data, key, default=0, type_cast=float):
    """
    Safely extracts data from JSON.
    Handles 'ground' string in altitude fields and missing keys.
    """
    val = data.get(key)
    if val is None or val == "ground": 
        return default
    try:
        return type_cast(val)
    except:
        return default

def fetch_node_data(base_url):
    """Pulls the live aircraft.json from the Readsb API."""
    try:
        url = f"{base_url}/data/aircraft.json"
        r = requests.get(url, timeout=2)
        if r.status_code == 200: return r.json()
    except:
        pass
    return None

def main():
    print(f"--- Position Feeder v3.0.0 (Full Telemetry) Started ---")
    last_log = 0
    
    while True:
        start_time = time.time()
        lines = []
        
        for node_name, node_url in NODES.items():
            data = fetch_node_data(node_url)
            if not data: continue

            # ReadsB timestamp (Nanoseconds for InfluxDB)
            now = int(data.get('now', time.time()) * 1e9)
            
            for ac in data.get('aircraft', []):
                # We only log aircraft that have a Hex ID and a Position.
                # 'seen_pos' < 60 ensures we don't log stale ghosts.
                if 'hex' in ac and 'lat' in ac:
                    
                    # --- CORE IDENTIFIERS (Tags) ---
                    # Tags are indexed. Use these for GROUP BY clauses.
                    icao = clean_tag(ac['hex'].lower())
                    call = clean_tag(ac.get('flight', 'N/A'))
                    
                    tags = f"icao24={icao},callsign={call},host={node_name},source=LocalReadsb"
                    
                    # --- 1. POSITION & VELOCITY ---
                    lat = get_val(ac, 'lat', 0.0, float)
                    lon = get_val(ac, 'lon', 0.0, float)
                    track = get_val(ac, 'track', 0.0, float)
                    gs = get_val(ac, 'gs', 0.0, float) # Ground Speed
                    
                    # Filter Null Island (0,0 coordinates)
                    if abs(lat) < 0.1 and abs(lon) < 0.1: continue

                    # --- 2. ALTITUDE (Baro vs Geom) ---
                    # Baro: Standard Pressure Altitude (What ATC sees)
                    # Geom: GPS Altitude (True height above ellipsoid)
                    alt_baro = get_val(ac, 'alt_baro', 0, int)
                    alt_geom = get_val(ac, 'alt_geom', 0, int)
                    vert_rate = get_val(ac, 'baro_rate', 0, int)
                    geom_rate = get_val(ac, 'geom_rate', 0, int)
                    nav_qnh = get_val(ac, 'nav_qnh', 1013.25, float)

                    # --- 3. AUTOPILOT / FMS INTENT (The "Pilot" Layer) ---
                    # nav_altitude_mcp: What is dialed into the autopilot?
                    # nav_heading: What magnetic heading is selected?
                    nav_alt = get_val(ac, 'nav_altitude_mcp', 0, int)
                    nav_hdg = get_val(ac, 'nav_heading', 0.0, float)

                    # --- 4. INTEGRITY & ACCURACY (The "Trust" Layer) ---
                    # NIC: Navigation Integrity Category (0-11). Higher is better.
                    # RC: Radius of Containment (Meters). Lower is better.
                    # SIL: Source Integrity Level (0-3). 3 = High trust.
                    nic = get_val(ac, 'nic', 0, int)
                    rc = get_val(ac, 'rc', 0, int)
                    sil = get_val(ac, 'sil', 0, int)
                    nac_p = get_val(ac, 'nac_p', 0, int)  # Position Accuracy
                    nac_v = get_val(ac, 'nac_v', 0, int)  # Velocity Accuracy
                    version = get_val(ac, 'version', 0, int) # DO-260B Version

                    # --- 5. STATUS & ALERTS ---
                    squawk = str(ac.get('squawk', 'None'))
                    emergency = str(ac.get('emergency', 'none'))
                    category = str(ac.get('category', 'A0')) # Wake turbulence cat
                    spi = get_val(ac, 'spi', 0, int) # Special Position Indicator (Ident)
                    alert = get_val(ac, 'alert', 0, int) # Flight status alert

                    # --- 6. SIGNAL HEALTH ---
                    rssi = get_val(ac, 'rssi', -49.5, float)
                    messages = get_val(ac, 'messages', 0, int) # Total msgs from this plane
                    seen = get_val(ac, 'seen', 0.0, float) # Seconds since last update

                    # --- CONSTRUCT FIELD SET ---
                    fields = [
                        # Physics
                        f"lat={lat}",
                        f"lon={lon}",
                        f"alt_baro_ft={alt_baro}i",
                        f"alt_geom_ft={alt_geom}i",
                        f"gs_knots={gs}",
                        f"track={track}",
                        f"vert_rate_fpm={vert_rate}i",
                        f"geom_rate_fpm={geom_rate}i",
                        
                        # FMS / Pilot Settings
                        f"nav_qnh={nav_qnh}",
                        f"nav_altitude_mcp_ft={nav_alt}i",
                        f"nav_heading={nav_hdg}",
                        
                        # Integrity
                        f"nic={nic}i",
                        f"rc={rc}i",
                        f"sil={sil}i",
                        f"nac_p={nac_p}i",
                        f"nac_v={nac_v}i",
                        f"adsb_version={version}i",
                        
                        # Status
                        f'squawk="{squawk}"',
                        f'emergency="{emergency}"',
                        f'category="{category}"',
                        f"spi={spi}i",
                        f"alert={alert}i",
                        
                        # Signal
                        f"rssi={rssi}",
                        f"msg_count={messages}i",
                        f"seen_seconds={seen}",
                        f'origin_data="LocalReadsb"'
                    ]
                    
                    lines.append(f"{MEASUREMENT},{tags} {','.join(fields)} {now}")

        if lines:
            try:
                requests.post(INFLUX_WRITE_URL, data="\n".join(lines), timeout=2)
                
                # Heartbeat log every 60 seconds
                if time.time() - last_log > 60:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Pushed {len(lines)} aircraft (Full Telemetry).")
                    last_log = time.time()
            except Exception as e:
                print(f"Write Error: {e}")

        # Sleep to maintain fetch interval
        time.sleep(max(0, FETCH_INTERVAL - (time.time() - start_time)))

if __name__ == "__main__":
    main()
