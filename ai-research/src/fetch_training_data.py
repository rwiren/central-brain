#!/usr/bin/env python3
# ==============================================================================
# DATA HARVESTER v2.0.0
# ==============================================================================
# Author:      RW / Central Brain Project
# Description: Extracts high-volume flight telemetry from InfluxDB for AI training.
#              Formats timestamps and cleans data for LSTM/Autoencoder models.
#
# 📋 CHANGELOG:
#   v1.0: Initial PoC (24h window).
#   v1.1: Fixed ISO8601 timestamp parsing error in Pandas.
#   v2.0: (2025-12-02 04:15)
#         - Added timestamped filenames to prevent overwrites.
#         - Added 'datasets/' directory management.
#         - Added execution timer and detailed logging.
#         - Scaled to 7-Day window for production model training.
# ==============================================================================

import pandas as pd
from influxdb import InfluxDBClient
import os
import sys
import time
from datetime import datetime

__version__ = "2.0.0"
__updated__ = "2025-12-02 04:15"

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# Central Brain IP (RPi5)
INFLUX_HOST = '192.168.1.134' 
INFLUX_PORT = 8086
DB_NAME = 'readsb'

# Training Window: "7d" for the final model, "24h" for quick tests
TIME_WINDOW = "7d" 

# Output Configuration
OUTPUT_DIR = "datasets"
TIMESTAMP_STR = datetime.now().strftime("%Y%m%d_%H%M")
OUTPUT_FILE = f"{OUTPUT_DIR}/training_data_{TIME_WINDOW}_{TIMESTAMP_STR}.csv"

def log(msg):
    """Helper for timestamped logging"""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")

def main():
    print("="*60)
    print(f"🦅 CENTRAL BRAIN DATA HARVESTER v{__version__}")
    print(f"📅 Last Updated: {__updated__}")
    print("="*60)

    # 1. Setup Environment
    if not os.path.exists(OUTPUT_DIR):
        log(f"Creating output directory: {OUTPUT_DIR}/")
        os.makedirs(OUTPUT_DIR)

    # 2. Connect to Database
    log(f"🔌 Connecting to Central Brain ({INFLUX_HOST})...")
    try:
        client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
        client.switch_database(DB_NAME)
    except Exception as e:
        log(f"❌ Connection Failed: {e}")
        sys.exit(1)

    # 3. Execute Query
    log(f"📥 Fetching last {TIME_WINDOW} of flight telemetry...")
    log("   (This may take 1-3 minutes for large datasets...)")
    
    start_time = time.time()

    # Filter: Only moving planes (>50kts) to remove ground noise
    query = f"""
        SELECT "lat", "lon", "alt_baro_ft", "gs_knots", "track", "v_rate_fpm"
        FROM "local_aircraft_state"
        WHERE time > now() - {TIME_WINDOW}
        AND "gs_knots" > 50
        GROUP BY "icao24"
    """

    try:
        result = client.query(query)
    except Exception as e:
        log(f"❌ Query Failed: {e}")
        sys.exit(1)

    # 4. Process Data
    data_points = []
    for (name, tags), points in result.items():
        icao = tags.get('icao24')
        for p in points:
            p['icao'] = icao
            data_points.append(p)

    if not data_points:
        log("⚠️ No data found! Check your time window or database connection.")
        sys.exit(0)

    log(f"🔄 Processing {len(data_points)} records into DataFrame...")
    
    df = pd.DataFrame(data_points)
    
    # Fix Timestamps (Critical for LSTM sequencing)
    # Explicitly use ISO8601 to handle the 'Z' UTC marker
    df['time'] = pd.to_datetime(df['time'], format='ISO8601')
    
    # Sort: Primary by Plane (ICAO), Secondary by Time
    df = df.sort_values(by=['icao', 'time'])

    # 5. Save Output
    log(f"💾 Saving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)

    # 6. Summary
    elapsed = time.time() - start_time
    log("-" * 30)
    log(f"✅ SUCCESS")
    log(f"⏱️ Time Elapsed: {elapsed:.2f} seconds")
    log(f"📊 Total Rows:  {len(df)}")
    log(f"📂 File Path:   {os.path.abspath(OUTPUT_FILE)}")
    print("-" * 30)
    print(df.head())

if __name__ == "__main__":
    main()
