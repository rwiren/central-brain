#!/usr/bin/env python3
"""
Script Name: inspect_raw_data.py
Description: Deep Forensic Tool.
             1. Lists ALL Measurements (Tables).
             2. Dumps the last 3 RAW records for every table.
             3. Checks specifically for 'host' tags to prove if data is Anonymous.
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     5.0.0
"""

import urllib.request
import urllib.parse
import json
import sys
import time

# --- Configuration ---
TARGET_HOST = "192.168.1.134"
PORT = "8086"
DB_NAME = "readsb"

def execute_query(query):
    url = f"http://{TARGET_HOST}:{PORT}/query?db={DB_NAME}&pretty=true"
    try:
        data = urllib.parse.urlencode({'q': query}).encode('ascii')
        with urllib.request.urlopen(url, data=data) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def print_series(series_list):
    if not series_list:
        print("   [Empty Table]")
        return

    for series in series_list:
        columns = series['columns']
        values = series['values']
        
        # Print Header
        print(f"   Columns: {columns}")
        
        # Print Rows
        for row in values:
            # Format timestamp for readability if possible
            print(f"   Row:     {row}")

def main():
    print("========================================================")
    print(f"   DEEP DATA INSPECTOR v5.0")
    print(f"   Target: {TARGET_HOST}")
    print("========================================================")

    # 1. Get List of Tables
    print("\n>>> Fetching Measurement List...")
    m_data = execute_query("SHOW MEASUREMENTS")
    
    if 'results' not in m_data or 'series' not in m_data['results'][0]:
        print("🔴 CRITICAL: Database is empty or unreachable.")
        sys.exit(1)
        
    measurements = [x[0] for x in m_data['results'][0]['series'][0]['values']]
    print(f"✅ Found {len(measurements)} tables: {measurements}")

    # 2. Iterate and Dump
    for m in measurements:
        print(f"\n--------------------------------------------------------")
        print(f"   TABLE: {m}")
        print(f"--------------------------------------------------------")
        
        # Query A: The Absolute Latest 3 Records
        q_latest = f"SELECT * FROM \"{m}\" ORDER BY time DESC LIMIT 3"
        res_latest = execute_query(q_latest)
        
        # Query B: Check for Identity (Group by Host)
        # This proves if 'host' tag exists or is missing
        q_host = f"SELECT * FROM \"{m}\" GROUP BY \"host\" ORDER BY time DESC LIMIT 1"
        res_host = execute_query(q_host)
        
        # Display Logic
        if 'results' in res_latest and 'series' in res_latest['results'][0]:
            print("   [LATEST 3 RECORDS]")
            print_series(res_latest['results'][0]['series'])
            
            # Check if 'host' column exists in the raw data
            cols = res_latest['results'][0]['series'][0]['columns']
            if "host" in cols:
                print("\n   ✅ 'host' tag detected in columns.")
            else:
                # If not in columns, maybe it's a tag key?
                print("\n   ⚠️ 'host' column NOT visible in simple select.")
                
            if 'results' in res_host and 'series' in res_host['results'][0]:
                 print("\n   [IDENTITY CHECK: Data per Host]")
                 for s in res_host['results'][0]['series']:
                     tags = s.get('tags', {})
                     print(f"   -> Host Tag detected: {tags.get('host', 'None')}")
            else:
                 print("\n   🔴 IDENTITY FAILURE: Unable to group by 'host'. Data is likely anonymous.")

        else:
            print("   [NO DATA]")

    print("\n========================================================")
    print("   INSPECTION COMPLETE")
    print("========================================================")

if __name__ == "__main__":
    main()
