#!/usr/bin/env python3
"""
Script Name: diagnose_feed_death.py
Description: System Forensic Tool.
             1. Calculates exactly how long the 'Truth Feed' has been dead.
             2. Validates that the new 'RTK/GPS' stream is actively alive.
             3. Checks for 'Physics Alerts' (Spoofing Detections) generated 
                before the death.
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     1.1.0
"""

import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone

# --- Configuration ---
INFLUX_HOST = "192.168.1.134"
PORT = "8086"
DB_NAME = "readsb"

def execute_query(query):
    url = f"http://{INFLUX_HOST}:{PORT}/query?db={DB_NAME}&pretty=true"
    try:
        data = urllib.parse.urlencode({'q': query}).encode('ascii')
        with urllib.request.urlopen(url, data=data) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def parse_time(timestamp_str):
    # InfluxDB returns ISO8601 usually like '2025-12-04T02:55:41Z'
    try:
        # Python 3.7+ handles 'Z' with fromisoformat, but let's be safe
        ts = timestamp_str.replace('Z', '+00:00')
        return datetime.fromisoformat(ts)
    except:
        return None

def check_heartbeat(measurement, name):
    print(f"--- Checking Pulse: {name} ('{measurement}') ---")
    
    # Get the very last record
    q = f"SELECT * FROM \"{measurement}\" ORDER BY time DESC LIMIT 1"
    res = execute_query(q)
    
    if 'results' in res and 'series' in res['results'][0]:
        # Extract time
        cols = res['results'][0]['series'][0]['columns']
        vals = res['results'][0]['series'][0]['values'][0]
        time_idx = cols.index('time')
        last_seen = vals[time_idx]
        
        # Calc downtime
        last_dt = parse_time(last_seen)
        now_dt = datetime.now(timezone.utc)
        
        if last_dt:
            delta = now_dt - last_dt
            minutes = int(delta.total_seconds() / 60)
            
            print(f"   Last Heartbeat: {last_seen}")
            print(f"   Time Since:     {minutes} minutes")
            
            if minutes < 5:
                print("   ❤️  STATUS: ALIVE")
            elif minutes < 60:
                print("   ⚠️  STATUS: LAGGING")
            else:
                print("   💀  STATUS: DEAD (Stalled)")
        
        # Architecture Check (Bonus)
        if measurement == "gps_tpv":
            try:
                epx_idx = cols.index('epx')
                print(f"   RTK Accuracy:   {vals[epx_idx]}m (If < 1.0m, RTK is working!)")
            except:
                pass
                
    else:
        print("   ❌ STATUS: NEVER SEEN (Empty Table)")

def main():
    print("========================================================")
    print(f"   SYSTEM PULSE CHECK v1.1")
    print("========================================================")
    
    # 1. The Problem Child (Truth Data)
    check_heartbeat("global_aircraft_state", "Truth Feed (OpenSky/FR24)")
    print("")
    
    # 2. The New Architecture (GPS/RTK)
    check_heartbeat("gps_tpv", "Keimola Grid (GPS/RTK)")
    print("")

    # 3. The Result (Spoofing Alerts)
    check_heartbeat("security_alerts", "Spoofing Detection Engine")

    print("\n========================================================")
    print("   RECOMMENDATION:")
    print("========================================================")
    print("   If 'Truth Feed' is DEAD (> 60 mins):")
    print("   1. Check the logs of your 'system-observer' or 'autohupr' container.")
    print("      (One of these is likely running the fetch script).")
    print("   2. API Rate Limit might be hit (OpenSky free tier resets daily).")

if __name__ == "__main__":
    main()
