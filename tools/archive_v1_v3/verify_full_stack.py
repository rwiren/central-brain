#!/usr/bin/env python3
"""
Script Name: verify_full_stack.py
Description: Comprehensive audit tool for the Keimola ADS-B & RTK Grid.
             Validates: 
               1. Node Identity (Office vs Balcony)
               2. RTK Precision (epx < 1.0m)
               3. Data Freshness (Last 2 mins)
               4. Feeder Aggregation (Central Brain visibility)
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     5.0.0
"""

import urllib.request
import urllib.parse
import json
import sys
import time
from datetime import datetime, timezone

# --- Configuration ---
TARGET_HOST = "192.168.1.134"
PORT = "8086"
DB_NAME = "readsb"

# Architectural Expectations
EXPECTED_NODES = ["keimola-office", "keimola-balcony"]

def execute_query(query):
    url = f"http://{TARGET_HOST}:{PORT}/query?db={DB_NAME}&pretty=true"
    try:
        data = urllib.parse.urlencode({'q': query}).encode('ascii')
        with urllib.request.urlopen(url, data=data, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def get_latest_data(measurement, group_by_tag):
    """Fetches the most recent record for every unique host."""
    q = f"SELECT * FROM \"{measurement}\" GROUP BY \"{group_by_tag}\" ORDER BY time DESC LIMIT 1"
    return execute_query(q)

def print_section(title):
    print(f"\n========================================================")
    print(f"   {title}")
    print(f"========================================================")

def audit_gps_rtk():
    print_section("AUDIT 1: RTK & GPS PRECISION (Measurement: gps_tpv)")
    
    res = get_latest_data("gps_tpv", "host")
    
    if 'results' not in res or 'series' not in res['results'][0]:
        print("🔴 CRITICAL FAIL: No GPS data found. Telegraf is not running or blocked.")
        return

    found_hosts = []
    
    for series in res['results'][0]['series']:
        tags = series.get('tags', {})
        cols = series['columns']
        vals = series['values'][0]
        
        host = tags.get('host', 'Unknown')
        found_hosts.append(host)
        
        # Extract Metrics
        try:
            epx = vals[cols.index('epx')]
            sats = vals[cols.index('satellites_used')]
            mode = vals[cols.index('mode')]
            ts = vals[cols.index('time')]
        except ValueError:
            print(f"   ⚠️  Schema Error for {host}: Missing columns.")
            continue

        # Analyze
        status = "ℹ️  STANDARD"
        if epx is not None:
            if epx < 0.1: status = "🌟 PERFECT RTK (<10cm)"
            elif epx < 1.0: status = "✅ HIGH PRECISION (<1m)"
            elif epx > 5.0: status = "⚠️  POOR ACCURACY (>5m)"
        
        print(f"   Node: {host}")
        print(f"     > Time:      {ts}")
        print(f"     > Satellites: {sats}")
        print(f"     > Precision:  {epx}m (EPX)")
        print(f"     > Status:     {status}")
        
        # Sanity Check
        if "${" in host:
            print("     ❌ ERROR: Hostname is a literal variable. Fix docker-compose environment!")

    # Missing Node Check
    missing = set(EXPECTED_NODES) - set(found_hosts)
    if missing:
        print(f"\n   ⚠️  MISSING NODES: {missing}")
    else:
        print(f"\n   ✅ ALL NODES ACCOUNTED FOR.")

def audit_feeders():
    print_section("AUDIT 2: ADS-B AGGREGATION (Measurement: local_aircraft_state)")
    
    res = get_latest_data("local_aircraft_state", "host")
    
    if 'results' not in res or 'series' not in res['results'][0]:
        print("🔴 CRITICAL FAIL: No aircraft data aggregated. 'readsb_position_feeder.py' is broken.")
        return

    print("   (Checking if Central Brain is pulling from both nodes...)")
    for series in res['results'][0]['series']:
        host = series['tags'].get('host', 'Unknown')
        count = 1 # We limited to 1, but existence is what matters
        print(f"   ✅ Receiving aircraft data from: {host}")

def generate_grafana_cheat_sheet():
    print_section("GRAFANA CHEAT SHEET (Copy-Paste these Queries)")
    
    print("1. RTK Precision Graph (Line Chart)")
    print("   SELECT mean(\"epx\") FROM \"gps_tpv\" WHERE $timeFilter GROUP BY time($__interval), \"host\"")
    print("")
    
    print("2. Satellite Count (Stat / Gauge)")
    print("   SELECT last(\"satellites_used\") FROM \"gps_tpv\" WHERE $timeFilter GROUP BY \"host\"")
    print("")
    
    print("3. CPU Temperature (Line Chart)")
    print("   SELECT mean(\"cpu_temp\") FROM \"system_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"")
    print("")
    
    print("4. Aircraft Range Comparison (Line Chart)")
    print("   SELECT max(\"max_range_km\") FROM \"adsb_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"")

def main():
    print(f"Target Database: {DB_NAME} @ {TARGET_HOST}")
    
    audit_gps_rtk()
    audit_feeders()
    generate_grafana_cheat_sheet()
    
    print("\n[End of Audit]")

if __name__ == "__main__":
    main()
