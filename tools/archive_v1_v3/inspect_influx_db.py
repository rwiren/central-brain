# ==============================================================================
# TOOL: InfluxDB Deep Inspector
# DESCRIPTION: Dumps schema and recent data to find where metrics are landing.
# ==============================================================================

import requests
import json
from datetime import datetime

# --- CONFIGURATION ---
HOST = "192.168.1.134"
PORT = 8086
DB   = "readsb"
USER = "admin"  # If you set INFLUX_USER in dashboard
PASS = "admin"  # If you set INFLUX_PASSWORD or TOKEN in dashboard

def query(q):
    url = f"http://{HOST}:{PORT}/query"
    try:
        # Try with auth
        r = requests.get(url, params={'db': DB, 'q': q}, auth=(USER, PASS), timeout=5)
        
        # If 401/403, try without auth (in case auth isn't actually enabled on DB)
        if r.status_code in [401, 403]:
            print(f"(!) Auth failed with user '{USER}'. Trying anonymous...")
            r = requests.get(url, params={'db': DB, 'q': q}, timeout=5)

        if r.status_code != 200:
            return f"ERROR: {r.status_code} - {r.text}"
        return r.json()
    except Exception as e:
        return f"CRASH: {str(e)}"

print(f"\n=== INFLUXDB INSPECTOR: {datetime.now().strftime('%H:%M:%S')} ===")
print(f"Target: {HOST}:{PORT} (DB: {DB})\n")

# 1. List Measurements (Tables)
print("--- 1. MEASUREMENTS FOUND ---")
data = query("SHOW MEASUREMENTS")
measurements = []

if isinstance(data, dict) and 'results' in data:
    if 'series' in data['results'][0]:
        for m in data['results'][0]['series'][0]['values']:
            measurements.append(m[0])
            print(f"  - {m[0]}")
    else:
        print("  (No measurements found - Database is empty!)")
else:
    print(f"  (Query Failed: {data})")

# 2. List Series (Unique Tags)
if measurements:
    print("\n--- 2. ACTIVE SENSORS (TAGS) ---")
    # Check distinct sensor_ids
    tag_data = query("SHOW TAG VALUES WITH KEY = \"sensor_id\"")
    if 'series' in tag_data['results'][0]:
        print("  Found 'sensor_id' tags:")
        for t in tag_data['results'][0]['series'][0]['values']:
            print(f"    > {t[1]}")
    else:
        print("  (!) No 'sensor_id' tags found. Checking 'host' tag...")
        host_data = query("SHOW TAG VALUES WITH KEY = \"host\"")
        if 'series' in host_data['results'][0]:
             for t in host_data['results'][0]['series'][0]['values']:
                print(f"    > host: {t[1]}")

# 3. Sample Data
if measurements:
    print("\n--- 3. RECENT DATA SAMPLES ---")
    # Check GPS data first
    target_meas = "gpsd_tpv" if "gpsd_tpv" in measurements else measurements[0]
    
    print(f"Sampling '{target_meas}':")
    sample = query(f"SELECT * FROM \"{target_meas}\" ORDER BY time DESC LIMIT 1")
    
    if 'series' in sample['results'][0]:
        cols = sample['results'][0]['series'][0]['columns']
        vals = sample['results'][0]['series'][0]['values'][0]
        for i, col in enumerate(cols):
            print(f"  {col}: {vals[i]}")
    else:
        print("  (Measurement exists but has no data?)")

print("\n==================================================")
