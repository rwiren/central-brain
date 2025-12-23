"""
================================================================================
SCRIPT: extract_training_data.py
DESCRIPTION: 
    Data Extraction Pipeline for InfluxDB v1.8 (Legacy).
    Designed for Level 4 AI Training Data Collection.
    
    - Auto-discovers all measurements (tables) in the database.
    - Chunks data by 24-hour periods to ensure stability.
    - Exports strictly formatted CSVs for Data Science/ML ingestion.

AUTHOR: System Architect
REVISION: 2.0.0 (Protocol Downgrade to InfluxQL)
DATE: 2025-12-17
================================================================================
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from influxdb import InfluxDBClient
import io

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CONFIG = {
    "HOST": "192.168.1.134",
    "PORT": 8086,
    "DATABASE": "readsb",
    
    # Auth (Leave empty if no auth is set on your local network)
    "USERNAME": "", 
    "PASSWORD": "",
    
    "OUTPUT_DIR": "./dataset_dump_v1",
    "DAYS_TO_EXPORT": 7,  # Look back 7 days
}

# ==============================================================================
# FUNCTIONS
# ==============================================================================

def get_client():
    return InfluxDBClient(
        host=CONFIG['HOST'],
        port=CONFIG['PORT'],
        username=CONFIG['USERNAME'],
        password=CONFIG['PASSWORD'],
        database=CONFIG['DATABASE']
    )

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_measurements(client):
    """Retrieves a list of all tables (measurements) in the DB."""
    try:
        print("  > Discovering measurements...")
        result = client.query("SHOW MEASUREMENTS")
        measurements = list(result.get_points())
        names = [m['name'] for m in measurements]
        print(f"  > Found {len(names)} measurements: {names}")
        return names
    except Exception as e:
        print(f"  [ERROR] Failed to list measurements: {e}")
        return []

def extract_measurement_chunk(client, measurement, date_str):
    """
    Downloads one day of data for a specific measurement.
    """
    # Calculate start/end for the query (InfluxQL format)
    # We treat date_str as the start of the day
    start_time = f"{date_str} 00:00:00"
    end_time = f"{date_str} 23:59:59"
    
    query = f"SELECT * FROM \"{measurement}\" WHERE time >= '{start_time}' AND time <= '{end_time}'"
    
    try:
        # Request data as a Pandas DataFrame directly
        # 'chunked=True' prevents server memory overload
        chunks = client.query(query, chunked=True, chunk_size=10000)
        
        data_frames = []
        # InfluxDBClient chunked response returns a generator of ResultSet
        # We need to iterate and convert points to DF
        for chunk in chunks:
            df_chunk = pd.DataFrame(list(chunk.get_points(measurement=measurement)))
            if not df_chunk.empty:
                data_frames.append(df_chunk)
        
        if not data_frames:
            return None

        return pd.concat(data_frames)

    except Exception as e:
        print(f"    [WARN] chunk query failed for {measurement}: {e}")
        return None

def main():
    print("--- AI TRAINING DATA EXTRACTOR (v1 InfluxQL) ---")
    print(f"Target: {CONFIG['HOST']}:{CONFIG['PORT']} | DB: {CONFIG['DATABASE']}")
    
    ensure_dir(CONFIG['OUTPUT_DIR'])
    client = get_client()

    # 1. Discovery Phase
    measurements = get_measurements(client)
    if not measurements:
        print("[FATAL] No data tables found. Check database name.")
        return

    # 2. Time Iteration Phase
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=CONFIG['DAYS_TO_EXPORT'])
    
    current_date = start_date
    total_files = 0

    while current_date < end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"\nProcessing Date: {date_str}")
        
        # 3. Extraction Phase (Per Measurement)
        for meas in measurements:
            print(f"  > Extracting table: {meas}...")
            df = extract_measurement_chunk(client, meas, date_str)
            
            if df is not None and not df.empty:
                # Save as CSV
                filename = f"{CONFIG['OUTPUT_DIR']}/{meas}_{date_str}.csv"
                df.to_csv(filename, index=False)
                print(f"    [SUCCESS] Saved {len(df)} rows -> {filename}")
                total_files += 1
            else:
                print(f"    [INFO] No data.")
        
        current_date += timedelta(days=1)

    print("-" * 50)
    print(f"Extraction Complete. Files created: {total_files}")
    print(f"Location: {os.path.abspath(CONFIG['OUTPUT_DIR'])}")

if __name__ == "__main__":
    main()
