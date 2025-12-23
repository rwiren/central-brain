#!/usr/bin/env python3
"""
Script: physics_test.py
Version: 2.1.0 (Fix: Influx Protocol Types)
Description: 
    Injects impossible flight data to test PhysicsGuard.
    - Adds 'i' suffix to integers to prevent HTTP 400 Type Errors.
"""

import requests
import time

# --- CONFIGURATION ---
INFLUX_HOST = "192.168.1.134"
INFLUX_PORT = 8086
DB_NAME = "readsb"
WRITE_URL = f"http://{INFLUX_HOST}:{INFLUX_PORT}/write?db={DB_NAME}"

MEASUREMENT = "local_aircraft_state" 
TARGET_ICAO = "TEST01"
TARGET_CALL = "DARKSTAR"

def inject_point(speed_kts):
    mach = speed_kts / 660.0
    
    # Influx Line Protocol Rules:
    # - Integers MUST have 'i' suffix (e.g., 50000i) if the DB expects integer.
    # - Floats are standard (e.g. 400.0).
    
    tags = f"icao24={TARGET_ICAO},callsign={TARGET_CALL},host=simulation"
    
    # CRITICAL FIX: Added 'i' to alt_baro_ft and vert_rate
    # This tells InfluxDB "Treat these as Integers" to match the schema.
    fields = f"gs_knots={float(speed_kts)},alt_baro_ft=50000i,vert_rate=0i,lat=60.32,lon=24.83"
    
    timestamp = int(time.time() * 1e9)
    line = f"{MEASUREMENT},{tags} {fields} {timestamp}"
    
    try:
        r = requests.post(WRITE_URL, data=line)
        if r.status_code < 400:
            print(f"   > Injected: {speed_kts} kts (Mach {mach:.2f})")
        else:
            print(f"   > Write Failed: {r.status_code} ({r.text.strip()})")
    except Exception as e:
        print(f"   > Connection Error: {e}")

def main():
    print(f"--- PHYSICS BREACH TEST v2.1 ---")
    print(f"    Target: {INFLUX_HOST}")
    print(f"    Table:  {MEASUREMENT}")
    print("-" * 40)

    speeds = [400, 900, 1500, 2100, 3500, 5000] 
    
    for s in speeds:
        inject_point(s)
        time.sleep(1)
        
    print("-" * 40)
    print("TEST COMPLETE. Check Grafana 'Alerts' or run verify_all_measurements.py")

if __name__ == "__main__":
    main()
