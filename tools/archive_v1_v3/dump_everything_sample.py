import requests
import csv
import os
import time
from datetime import datetime

# ==============================================================================
# Script: dump_everything_sample.py
# Description: Dynamically discovers ALL measurements and dumps last 15m of data.
# Purpose: Full system audit for AI analysis.
# ==============================================================================

# CONFIGURATION
INFLUX_HOST = "http://192.168.1.134:8086"
DB_NAME = "readsb"
DURATION = "15m"  # Keep it short to avoid massive files
OUTPUT_DIR = "./dump_sample_15m"

def query_influx(q):
    params = {'db': DB_NAME, 'q': q, 'epoch': 's'}
    try:
        r = requests.get(f"{INFLUX_HOST}/query", params=params, timeout=30)
        if r.status_code == 200: return r.json()
    except Exception as e:
        print(f"⚠️ Query Error: {e}")
    return None

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"--- 🔍 Starting Full System Dump (Last {DURATION}) ---")
    print(f"Target: {INFLUX_HOST} ({DB_NAME})")

    # 1. Discover All Measurements (Tables)
    print("-> Discovering measurements...")
    m_data = query_influx("SHOW MEASUREMENTS")
    
    if not m_data or 'results' not in m_data or 'series' not in m_data['results'][0]:
        print("❌ No measurements found in database.")
        return

    measurements = [x[0] for x in m_data['results'][0]['series'][0]['values']]
    print(f"✅ Found {len(measurements)} measurements: {measurements}")

    summary_lines = []
    summary_lines.append(f"System Audit Report - {datetime.now()}")
    summary_lines.append(f"Duration: Last {DURATION}\n")

    # 2. Dump Each Measurement
    for m in measurements:
        print(f"-> Extracting '{m}'...")
        filename = f"{OUTPUT_DIR}/{m}.csv"
        
        # Select everything (*)
        data = query_influx(f'SELECT * FROM "{m}" WHERE time > now() - {DURATION}')
        
        if not data or 'results' not in data or 'series' not in data['results'][0]:
            print(f"   ⚠️ No data in last {DURATION}. Skipping.")
            summary_lines.append(f"Measurement: {m}\n  - Status: EMPTY (0 rows)\n")
            continue

        # Process Results
        series = data['results'][0]['series'][0]
        columns = series['columns']
        values = series['values']
        row_count = len(values)
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns) # Header
            writer.writerows(values) # Data
            
        print(f"   ✅ Saved {row_count} rows to {filename}")
        
        # Add to Summary Report
        summary_lines.append(f"Measurement: {m}")
        summary_lines.append(f"  - Rows: {row_count}")
        summary_lines.append(f"  - Columns ({len(columns)}): {', '.join(columns)}")
        summary_lines.append("")

    # 3. Write Summary Report
    with open(f"{OUTPUT_DIR}/_SUMMARY.txt", "w") as f:
        f.write("\n".join(summary_lines))

    print(f"\n✅ Dump Complete. Check the '{OUTPUT_DIR}' folder.")
    print(f"📄 Summary Report: {OUTPUT_DIR}/_SUMMARY.txt")

if __name__ == "__main__":
    main()
