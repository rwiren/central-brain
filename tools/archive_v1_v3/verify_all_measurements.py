#!/usr/bin/env python3
"""
Script: verify_all_measurements.py
Version: 1.1.0 (Fix: Robust Timestamp Parsing)
Description: 
    Performs a deep sanity check on EVERY measurement in InfluxDB.
    - Handles both ISO8601 (2025-...) and Epoch (176...) timestamps.
    - Correctly reports LIVE/STALE status.
"""

import requests
import json
import time
from datetime import datetime, timezone
import sys
import re

# --- CONFIGURATION ---
INFLUX_HOST = "192.168.1.134"
INFLUX_PORT = 8086
DB_NAME = "readsb"

def execute_query(q):
    try:
        url = f"http://{INFLUX_HOST}:{INFLUX_PORT}/query"
        # Request epoch timestamps for easier math
        params = {'db': DB_NAME, 'q': q, 'epoch': 's'}
        r = requests.get(url, params=params, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")
        sys.exit(1)
    return {}

def get_measurements():
    """Fetches list of all tables."""
    data = execute_query("SHOW MEASUREMENTS")
    measurements = []
    try:
        for series in data['results'][0]['series']:
            for value in series['values']:
                measurements.append(value[0])
    except:
        pass
    return sorted(measurements)

def check_measurement(name):
    # Get last record
    q = f'SELECT * FROM "{name}" ORDER BY time DESC LIMIT 1'
    data = execute_query(q)
    
    status = "🔴 EMPTY"
    lag_str = "-"
    source = "-"
    
    if data and 'results' in data and 'series' in data['results'][0]:
        series = data['results'][0]['series'][0]
        cols = series['columns']
        vals = series['values'][0]
        
        # 1. Calculate Lag
        time_idx = cols.index('time')
        last_ts = vals[time_idx] # Now guaranteed to be epoch seconds
        
        try:
            now_ts = time.time()
            delta = now_ts - last_ts
            
            if delta < 60:
                lag_str = f"{int(delta)}s ago"
                status = "🟢 LIVE"
            elif delta < 3600:
                lag_str = f"{int(delta/60)}m ago"
                status = "🟡 ACTIVE"
            else:
                lag_str = f"{int(delta/3600)}h ago"
                status = "🟠 STALE"
                
        except Exception:
            lag_str = "CalcErr"

        # 2. Identify Source (Host/Station/Source)
        if 'host' in cols and vals[cols.index('host')]:
            source = vals[cols.index('host')]
        elif 'station' in cols and vals[cols.index('station')]:
            source = vals[cols.index('station')]
        elif 'source' in cols and vals[cols.index('source')]:
            source = vals[cols.index('source')]
        elif 'icao' in cols and vals[cols.index('icao')]:
            source = f"ICAO:{vals[cols.index('icao')]}"
    
    return status, lag_str, source

def main():
    print(f"--- GLOBAL SANITY CHECK v1.1 @ {INFLUX_HOST} ---")
    print(f"    Scanning database '{DB_NAME}'...")
    
    tables = get_measurements()
    
    print(f"{'MEASUREMENT':<25} | {'STATUS':<8} | {'LAST SEEN':<10} | {'SOURCE'}")
    print("-" * 75)
    
    active_count = 0
    stale_count = 0
    
    for tbl in tables:
        status, lag, source = check_measurement(tbl)
        print(f"{tbl:<25} | {status:<8} | {lag:<10} | {source}")
        
        if "LIVE" in status or "ACTIVE" in status:
            active_count += 1
        elif "STALE" in status:
            stale_count += 1
            
    print("-" * 75)
    print(f"SUMMARY: {active_count} Active, {stale_count} Stale/Empty")

if __name__ == "__main__":
    main()
