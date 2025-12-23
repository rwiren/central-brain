#!/usr/bin/env python3
"""
Script Name: inspect_truth_sources.py
Description: Forensic tool to identify the sources of "Truth" data in InfluxDB.
             Inspects 'global_truth' and 'global_aircraft_state' for provider tags
             (e.g., source=opensky, source=fr24).
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     1.0.0

Usage:       python3 inspect_truth_sources.py
"""

import urllib.request
import urllib.parse
import json

# --- Configuration ---
INFLUX_HOST = "192.168.1.134"
PORT = "8086"
DB_NAME = "readsb"

# The suspected "Truth" tables
TARGETS = ["global_truth", "global_aircraft_state"]

def execute_query(query):
    url = f"http://{INFLUX_HOST}:{PORT}/query?db={DB_NAME}&pretty=true"
    try:
        data = urllib.parse.urlencode({'q': query}).encode('ascii')
        with urllib.request.urlopen(url, data=data) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def analyze_measurement(measurement):
    print(f"\n--- 🕵️‍♂️ Analyzing Measurement: {measurement} ---")
    
    # 1. Check for 'source' or 'provider' tags
    # This tells us WHO sent the data (OpenSky vs FR24)
    tag_keys_res = execute_query(f"SHOW TAG KEYS FROM \"{measurement}\"")
    
    tag_keys = []
    if 'results' in tag_keys_res and 'series' in tag_keys_res['results'][0]:
        tag_keys = [x[0] for x in tag_keys_res['results'][0]['series'][0]['values']]
        print(f"   Indexed Tags: {tag_keys}")
    else:
        print("   [!] No tags found (or empty table).")
        return

    # 2. Inspect Source Values
    # If a tag like 'source', 'origin', 'feeder', or 'host' exists, show its values.
    interesting_tags = ['source', 'provider', 'feed', 'origin', 'host']
    found_any = False
    
    for key in interesting_tags:
        if key in tag_keys:
            found_any = True
            print(f"   >> Found potential Source Key: '{key}'")
            vals = execute_query(f"SHOW TAG VALUES FROM \"{measurement}\" WITH KEY = \"{key}\"")
            try:
                values = [x[1] for x in vals['results'][0]['series'][0]['values']]
                print(f"      Values: {values}")
            except:
                print("      (No values found)")

    # 3. Data Sample
    print("\n   >> Latest Data Sample (Fields):")
    sample = execute_query(f"SELECT * FROM \"{measurement}\" ORDER BY time DESC LIMIT 1")
    try:
        cols = sample['results'][0]['series'][0]['columns']
        vals = sample['results'][0]['series'][0]['values'][0]
        # Print neat dict
        for c, v in zip(cols, vals):
            print(f"      {c}: {v}")
    except:
        print("      [!] Table appears empty.")

def main():
    print("========================================================")
    print(f"   TRUTH DATA INSPECTOR v1.0")
    print(f"   Database: {DB_NAME} @ {INFLUX_HOST}")
    print("========================================================")

    for t in TARGETS:
        analyze_measurement(t)

    print("\n========================================================")
    print("   ANALYSIS COMPLETE")
    print("========================================================")

if __name__ == "__main__":
    main()
