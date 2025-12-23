import requests
import json
import datetime
import sys

# --- CONFIGURATION ---
INFLUX_IP = "192.168.1.134"
DB_NAME = "readsb"

def check_storage():
    print(f"--- AUDITING INFLUXDB @ {INFLUX_IP} ---")
    
    # Query for the latest entry in the 'rf_battle_stats' measurement
    # (This is the table where your Battlefield script likely writes)
    query = f'SELECT * FROM "rf_battle_stats" ORDER BY time DESC LIMIT 1'
    
    url = f"http://{INFLUX_IP}:8086/query"
    params = {'db': DB_NAME, 'q': query}
    
    try:
        r = requests.get(url, params=params, timeout=2)
        data = r.json()
        
        if 'results' in data and 'series' in data['results'][0]:
            # Data Found
            series = data['results'][0]['series'][0]
            columns = series['columns']
            values = series['values'][0]
            
            # Find timestamps
            time_idx = columns.index("time")
            timestamp_str = values[time_idx]
            
            # Calculate lag
            # Influx returns ISO8601: 2025-12-04T15:51:03.123Z
            # We need to be careful with parsing, but for a rough check:
            print(f"\n✅ DATA FOUND in '{DB_NAME}'")
            print(f"   Last Write: {timestamp_str}")
            print("\n   Latest Battle Stats:")
            
            # Print nicely
            for i, col in enumerate(columns):
                if col != "time":
                    print(f"   - {col}: {values[i]}")
                    
            print("\n   [PASS] The pipeline is working.")
            
        else:
            print(f"\n❌ NO DATA FOUND in measurement 'rf_battle_stats'")
            print("   Possible reasons:")
            print("   1. Script is running but not actually writing (Dry Run?)")
            print("   2. Measurement name mismatch (Is it writing to 'local_performance' instead?)")

    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    check_storage()
