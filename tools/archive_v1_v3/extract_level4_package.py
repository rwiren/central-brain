import requests
import csv
import gzip
import os
import time
from datetime import datetime

# ==============================================================================
# Script: extract_level4_package.py
# Description: Exports Level 4 Telemetry (Intent + Integrity) for AI Training.
# Output: Compressed CSV (.csv.gz)
# ==============================================================================

# TARGET: Your Central Brain IP (Since you are running this from your Mac)
INFLUX_HOST = "http://192.168.1.134:8086"
DB_NAME = "readsb"

# The "Gold Standard" Level 4 columns
COLUMNS = [
    "time", "icao24", "callsign", "host",
    "lat", "lon", "alt_baro_ft", "gs_knots", "track", "vert_rate_fpm", # Physics
    "nav_altitude_mcp_ft", "nav_heading",                              # Pilot Intent
    "nic", "rc", "sil",                                                # Integrity
    "squawk", "emergency", "rssi"                                      # Status
]

def query_influx(query):
    params = {'db': DB_NAME, 'q': query, 'epoch': 's'}
    try:
        r = requests.get(f"{INFLUX_HOST}/query", params=params, timeout=120)
        if r.status_code == 200: return r.json()
    except Exception as e:
        print(f"Connection Error: {e}")
    return None

def main():
    # --- SMART DIRECTORY SELECTION ---
    # If /data exists (Balena/Linux), use it. Otherwise use local folder (Mac).
    if os.path.exists("/data") and os.access("/data", os.W_OK):
        target_dir = "/data/training_packages"
    else:
        target_dir = "./training_packages"

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Setup Filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{target_dir}/level4_flight_data_{timestamp}.csv.gz"
    
    print(f"--- Starting Level 4 Dump ---")
    print(f"Target Host: {INFLUX_HOST}")
    print(f"Output Path: {filename}")
    
    # Query
    print("Querying last 24 hours of telemetry (this may take 30s)...")
    
    # Construct query string dynamically
    field_cols = ", ".join([c for c in COLUMNS if c not in ["time", "icao24", "callsign", "host"]])
    query = f"""
        SELECT {field_cols}
        FROM local_aircraft_state 
        WHERE time > now() - 24h 
        GROUP BY "icao24", "callsign", "host"
    """
    
    data = query_influx(query)
    
    if not data or 'results' not in data:
        print("❌ No data found or connection failed.")
        return

    # Write Data
    print("Data received. Writing to file...")
    row_count = 0
    
    try:
        with gzip.open(filename, 'wt', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(COLUMNS) # Header
            
            for result in data['results']:
                if 'series' not in result: continue
                for series in result['series']:
                    tags = series.get('tags', {})
                    icao = tags.get('icao24', 'unknown')
                    call = tags.get('callsign', 'unknown')
                    host = tags.get('host', 'unknown')
                    
                    col_map = {name: i for i, name in enumerate(series['columns'])}
                    
                    for val in series['values']:
                        row = [val[0], icao, call, host]
                        
                        for col_name in COLUMNS[4:]:
                            idx = col_map.get(col_name)
                            row.append(val[idx] if idx is not None else "")
                        
                        writer.writerow(row)
                        row_count += 1
                        
        print(f"✅ Success! Exported {row_count} rows.")
        print(f"📦 File is ready at: {filename}")
        
    except Exception as e:
        print(f"❌ Error writing file: {e}")

if __name__ == "__main__":
    main()
