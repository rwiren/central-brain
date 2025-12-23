#!/usr/bin/env python3
"""
Script Name: find_active_hosts.py
Description: Scans InfluxDB for ANY host reporting data in the last 10 minutes.
             Used to debug "Missing Node" issues by revealing the actual hostnames
             being used by the devices.
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     1.0.0
"""

import urllib.request
import urllib.parse
import json
import datetime

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

def main():
    print("========================================================")
    print(f"   ACTIVE HOST DISCOVERY TOOL")
    print(f"   Scanning Last 10 Minutes of Data...")
    print("========================================================")

    # We check two measurements: 'gpsd_tpv' (GPS) and 'readsb' (ADSB Stats)
    measurements = ["gpsd_tpv", "readsb", "system_stats"]
    
    found_hosts = set()
    
    for m in measurements:
        print(f"\n>> Scanning Measurement: '{m}'")
        
        # Query: Show tags from the last 10 minutes
        q = f"SHOW TAG VALUES FROM \"{m}\" WITH KEY = \"host\" WHERE time > now() - 10m"
        res = execute_query(q)
        
        if 'results' in res and 'series' in res['results'][0]:
            values = res['results'][0]['series'][0]['values']
            print(f"   Found active hosts: {len(values)}")
            for v in values:
                hostname = v[1]
                print(f"   - {hostname}")
                found_hosts.add(hostname)
        else:
            print("   No active hosts found (Measurement empty or silence).")

    print("\n========================================================")
    print("   SUMMARY OF ACTIVE HOSTS")
    print("========================================================")
    
    if not found_hosts:
        print("❌ NO HOSTS DETECTED.")
        print("   Troubleshooting:")
        print("   1. Are the devices powered on?")
        print("   2. Did 'telegraf' crash? Check 'docker logs telegraf'")
        print("   3. Is the firewall blocking port 8086?")
    else:
        print(f"✅ The following names are currently writing to DB:")
        for h in found_hosts:
            print(f"   -> {h}")
            
        print("\n   Compare these names against your 'verify_site_migration.py' expectations.")

if __name__ == "__main__":
    main()
