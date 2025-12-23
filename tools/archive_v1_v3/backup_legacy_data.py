#!/usr/bin/env python3
"""
Script Name: backup_legacy_data.py
Description: Archival tool to dump InfluxDB history to CSV.
             Fixed URL encoding bug (v1.1.0).
             Added auto-detection for Container IDs.
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     1.1.0 (Bugfix Release)
"""

import urllib.request
import urllib.parse
import os
import time

# --- Configuration ---
INFLUX_HOST = "192.168.1.134"
PORT = "8086"
DB_NAME = "readsb"

# Primary Target (The name we HOPE is there)
PRIMARY_HOST = "keimola-tower"
# Secondary Target (The Container ID we saw in logs)
FALLBACK_HOST = "fd81b74"

MEASUREMENTS = [
    "gpsd_tpv",       # GPS History
    "readsb",         # Receiver Stats
    "system_stats",   # Hardware Health
    "aircraft"        # Flight Data
]

BACKUP_DIR = "./archive_keimola_tower"

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def export_csv(measurement, hostname):
    """Fetches data from InfluxDB and saves as CSV."""
    filename = f"{BACKUP_DIR}/{measurement}_{hostname}.csv"
    print(f"   > Querying '{measurement}' for host '{hostname}'...")
    
    query = f"SELECT * FROM \"{measurement}\" WHERE \"host\" = '{hostname}'"
    
    url = f"http://{INFLUX_HOST}:{PORT}/query"
    params = {
        'db': DB_NAME,
        'q': query
    }
    
    headers = {'Accept': 'application/csv'}

    try:
        # FIX: Ensure we use string, not bytes, for the URL
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        req = urllib.request.Request(full_url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            line_count = len(content.strip().split('\n'))
            
            # InfluxDB CSV always returns a header line. 
            # If line_count <= 1, it means no actual data rows.
            if line_count <= 1:
                return False # Indicate empty
            else:
                print(f"     [+] Found {line_count-1} records. Saving...")
                with open(filename, 'w') as f:
                    f.write(content)
                return True
                
    except urllib.error.HTTPError as e:
        print(f"     [!] HTTP Error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"     [!] Error: {e}")
        return False

def main():
    print("========================================================")
    print(f"   LEGACY DATA ARCHIVER v1.1.0")
    print(f"   Database: {DB_NAME} @ {INFLUX_HOST}")
    print("========================================================")
    
    ensure_dir(BACKUP_DIR)
    
    # 1. Try the nice hostname first
    print(f"\n--- Attempt 1: Hostname '{PRIMARY_HOST}' ---")
    data_found = False
    for m in MEASUREMENTS:
        if export_csv(m, PRIMARY_HOST):
            data_found = True
            
    # 2. If nothing found, try the ugly Container ID
    if not data_found:
        print(f"\n[!] No data found for '{PRIMARY_HOST}'.")
        print(f"--- Attempt 2: Fallback ID '{FALLBACK_HOST}' ---")
        for m in MEASUREMENTS:
            export_csv(m, FALLBACK_HOST)

    print("\n========================================================")
    print(f"   ARCHIVE COMPLETE")
    print(f"   Check folder: {BACKUP_DIR}/")
    print("========================================================")

if __name__ == "__main__":
    main()
