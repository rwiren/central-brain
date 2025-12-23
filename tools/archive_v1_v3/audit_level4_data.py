import requests
import sys
from datetime import datetime

# ==============================================================================
# Script: audit_level4_data.py
# Description: Checks if NEW "Level 4" fields are actually populating.
# ==============================================================================

INFLUX_HOST = "http://localhost:8086"
DB_NAME = "readsb"

# The specific new fields we want to verify
LEVEL_4_FIELDS = [
    "nav_altitude_mcp_ft", # Pilot Intent
    "nav_heading",         # Pilot Intent
    "nic",                 # Integrity
    "rc",                  # Integrity
    "sil",                 # Integrity
    "vert_rate_fpm",       # Physics
    "squawk",              # Status
    "rssi",                # Signal
    "emergency"            # Status
]

def query_count(measurement, field):
    """Counts non-null values for a specific field in the last hour."""
    q = f'SELECT count("{field}") FROM "{measurement}" WHERE time > now() - 1h'
    params = {'db': DB_NAME, 'q': q}
    try:
        r = requests.get(f"{INFLUX_HOST}/query", params=params)
        data = r.json()
        if 'results' in data and 'series' in data['results'][0]:
            return data['results'][0]['series'][0]['values'][0][1]
    except:
        pass
    return 0

def get_total_rows(measurement):
    """Counts total rows in the last hour."""
    return query_count(measurement, "lat") # Lat is always present

def main():
    print("--- 🔍 Level 4 Data Audit (Last 60 Minutes) ---")
    
    total_rows = get_total_rows("local_aircraft_state")
    print(f"Total Telemetry Points Processed: {total_rows}")
    
    if total_rows == 0:
        print("❌ No data found in the last hour. Check feeders!")
        sys.exit(1)

    print("\n--- 📡 Field Population Rates ---")
    print(f"{'Field Name':<25} | {'Count':<10} | {'Fill Rate':<10} | {'Status'}")
    print("-" * 65)

    for field in LEVEL_4_FIELDS:
        count = query_count("local_aircraft_state", field)
        rate = (count / total_rows) * 100
        
        status = "✅ Excellent"
        if rate < 5: status = "❌ CRITICAL"
        elif rate < 50: status = "⚠️ Low"
        
        # Adjust expectations for rare events
        if field == "emergency" and rate > 0: status = "⚠️ ALERT (Real Emergencies!)"
        if field == "emergency" and rate == 0: status = "✅ Normal (None)"

        print(f"{field:<25} | {count:<10} | {rate:>6.1f}%   | {status}")

    print("-" * 65)
    print("✅ Audit Complete.")

if __name__ == "__main__":
    main()
