import requests
import csv
import json
import gzip
import os
import shutil
from datetime import datetime

# ==============================================================================
# Script: create_golden_dataset.py
# Description: Generates a complete AI Training Bundle (Inputs + Truth + Meta).
# ==============================================================================

INFLUX_HOST = "http://192.168.1.134:8086"
DB_NAME = "readsb"
OUTPUT_DIR = "./golden_dataset_v1"

# --- 1. CONFIG: SENSOR METADATA (Crucial for AI Physics) ---
SENSOR_META = {
    "sensor_id": "central-brain-vantaa",
    "location": {
        "lat": 60.319555,
        "lon": 24.830819,
        "alt_msl_m": 45.0  # Estimated antenna height
    },
    "hardware": {
        "receiver": "RTL-SDR v3",
        "computer": "Raspberry Pi 4",
        "antenna": "Optimized 1090MHz"
    },
    "capabilities": ["pilot_intent", "integrity_metrics", "sensor_fusion"]
}

# --- 2. QUERY DEFINITIONS ---
QUERIES = {
    "X_local_telemetry": {
        "measurement": "local_aircraft_state",
        "fields": [
            "time", "icao24", "callsign", "lat", "lon", "alt_baro_ft", 
            "gs_knots", "track", "vert_rate_fpm", "nav_altitude_mcp_ft", 
            "nav_heading", "nic", "rc", "sil", "rssi", "squawk"
        ]
    },
    "Y_global_truth": {
        "measurement": "global_aircraft_state",
        "fields": [
            "time", "icao24", "callsign", "lat", "lon", "alt_baro_ft",
            "gs_knots", "track", "vert_rate_fpm", "origin_country"
        ]
    }
}

def query_influx(q):
    try:
        r = requests.get(f"{INFLUX_HOST}/query", params={'db': DB_NAME, 'q': q, 'epoch': 's'})
        if r.status_code == 200: return r.json()
    except Exception as e:
        print(f"Error: {e}")
    return None

def extract_csv(name, config, folder):
    print(f"-> Extracting {name}...")
    
    # Dynamic Query Construction
    cols = config['fields']
    # Exclude tags from SELECT (they come in via GROUP BY logic usually, or just implicitly)
    select_cols = ", ".join([c for c in cols if c not in ["time", "icao24", "callsign", "origin_country"]])
    
    # We select specific fields. Note: Tags like 'icao24' are returned in 'tags' object by Influx
    query = f'SELECT {select_cols} FROM {config["measurement"]} WHERE time > now() - 24h GROUP BY *'
    
    data = query_influx(query)
    if not data or 'results' not in data:
        print(f"   ⚠️ No data for {name}")
        return

    filepath = f"{folder}/{name}.csv"
    row_count = 0
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        
        for result in data['results']:
            if 'series' not in result: continue
            for series in result['series']:
                tags = series.get('tags', {})
                # Map columns
                col_map = {c: i for i, c in enumerate(series['columns'])}
                
                for val in series['values']:
                    row = []
                    for c in cols:
                        if c == "time": row.append(val[0])
                        elif c in tags: row.append(tags[c])
                        else:
                            idx = col_map.get(c)
                            row.append(val[idx] if idx is not None else "")
                    writer.writerow(row)
                    row_count += 1
    
    print(f"   ✅ Saved {row_count} rows.")

def create_readme(folder):
    content = """
# Secure Skies - Golden Training Dataset (v1)

## Overview
This dataset contains 24 hours of high-fidelity aviation telemetry from the Vantaa Receiver Node.
It is designed for training Level 4 AI models (Trajectory Prediction, Intent Analysis).

## Files
1. **X_local_telemetry.csv**: Raw sensor data (1-10Hz). Contains 'Pilot Intent' (nav_altitude).
2. **Y_global_truth.csv**: Validation data from OpenSky Network. Use for error drift calculation.
3. **metadata.json**: Receiver physical location and hardware specs.

## Key Terminology
- **nav_altitude_mcp_ft**: The altitude set on the autopilot panel (Pilot Intent).
- **nic (Navigation Integrity Category)**: 0-11 score of GPS trust. High is better.
- **rc (Radius of Containment)**: The 95% confidence radius of the position (meters).
    """
    with open(f"{folder}/README.md", "w") as f:
        f.write(content.strip())

def main():
    if os.path.exists(OUTPUT_DIR): shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    
    print(f"--- Generating Golden Dataset in {OUTPUT_DIR} ---")
    
    # 1. Extract Data
    for name, config in QUERIES.items():
        extract_csv(name, config, OUTPUT_DIR)
        
    # 2. Generate Metadata
    with open(f"{OUTPUT_DIR}/metadata.json", "w") as f:
        json.dump(SENSOR_META, f, indent=4)
        print("-> Generated metadata.json")

    # 3. Generate README
    create_readme(OUTPUT_DIR)
    print("-> Generated README.md")

    # 4. Zip it
    shutil.make_archive("secure_skies_golden_dataset", 'zip', OUTPUT_DIR)
    print("\n✅ Package Ready: secure_skies_golden_dataset.zip")

if __name__ == "__main__":
    main()
