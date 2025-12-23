#!/usr/bin/env python3
"""
Script Name: analyze_truth_distribution.py
Description: Deep scans the 'global_aircraft_state' table to determine 
             the REAL source of the data by counting the 'origin_data' field.
             (Workaround for InfluxQL inability to GROUP BY fields).
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     1.0.0
"""

import urllib.request
import urllib.parse
import json
from collections import Counter

# --- Configuration ---
INFLUX_HOST = "192.168.1.134"
PORT = "8086"
DB_NAME = "readsb"
MEASUREMENT = "global_aircraft_state"

def execute_query(query):
    url = f"http://{INFLUX_HOST}:{PORT}/query?db={DB_NAME}&pretty=true"
    try:
        data = urllib.parse.urlencode({'q': query}).encode('ascii')
        with urllib.request.urlopen(url, data=data) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")
        return {}

def main():
    print("========================================================")
    print(f"   TRUTH SOURCE AUDIT")
    print(f"   Scanning active table: {MEASUREMENT}")
    print("========================================================")

    # 1. Fetch 'origin_data' (The Field) and 'source' (The Tag) for last 1 hour
    print(">> Fetching last 1 hour of data...")
    # We select source (tag) and origin_data (field)
    q = f"SELECT \"source\", \"origin_data\" FROM \"{MEASUREMENT}\" WHERE time > now() - 1h"
    res = execute_query(q)

    if 'results' not in res or 'series' not in res['results'][0]:
        print("❌ NO DATA found in the last hour.")
        print("   Verification: Is the external feed container running?")
        return

    values = res['results'][0]['series'][0]['values']
    columns = res['results'][0]['series'][0]['columns']
    
    # Map column indices
    try:
        idx_source = columns.index('source')
        idx_origin = columns.index('origin_data')
    except ValueError:
        print(f"❌ Critical Schema Error: Columns missing. Found: {columns}")
        return

    # 2. Count Distributions
    stats = Counter()
    total = len(values)
    
    for row in values:
        s_tag = row[idx_source]
        o_field = row[idx_origin]
        signature = f"Tag: {s_tag} | Field: {o_field}"
        stats[signature] += 1

    # 3. Report
    print(f"\n✅ Analyzed {total} records.\n")
    print("DISTRIBUTION OF SOURCES:")
    print("------------------------------------------------")
    print(f"{'Signature (What InfluxDB sees)':<40} | {'Count':<10} | {'%':<5}")
    print("------------------------------------------------")
    
    for sig, count in stats.most_common():
        pct = round((count / total) * 100, 1)
        print(f"{sig:<40} | {count:<10} | {pct}%")

    print("------------------------------------------------")
    
    # 4. Recommendation
    if len(stats) > 1:
        print("\n[!] MIXED DATA DETECTED. You have multiple sources.")
    elif "FR24" in list(stats.keys())[0] and "OpenSky" in list(stats.keys())[0]:
        print("\n[!] MISLABELING DETECTED: Source is tagged 'FR24' but content is 'OpenSky'.")
        print("    Action: Update your Telegraf/Ingestor config to tag correctly.")

if __name__ == "__main__":
    main()
