#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System: Secure Skies - Raw Dump to CSV Extractor
Script: extract_csv_from_dump_v4.py
Description: A standalone utility for the AI Team to regenerate training data 
             from the raw InfluxDB Line Protocol (.lp) dump.
             
             Usage:
             1. Ensure 'central_brain_full_dump.lp' is in the same folder.
             2. Run: python3 extract_csv_from_dump_v4.py
             3. Output: 3 CSV files (Local, Global, Alerts).

Version: 4.0.0
Author: RW (Lead Solution Architect)
Date: 2025-12-18
"""

import sys
import datetime
import csv
import re
import os

# ================= Configuration =================
# The massive raw text file containing all sensor data
INPUT_FILE = 'central_brain_full_dump.lp'

# Target Training Window (The "Golden Week" + Antenna Move)
START_DATE = '2025-11-26'
END_DATE   = '2025-12-03'

# Output Filenames
OUT_LOCAL = 'secure_skies_local_v2.csv'
OUT_GLOBAL = 'secure_skies_global_v2.csv'
OUT_ALERTS = 'secure_skies_alerts_v2.csv'

# Feature Mapping (Raw Influx Field -> Clean CSV Column)
# This standardizes the data for the AI model.
FEATURE_MAP = {
    'icao24': 'ICAO24',             # Unique Aircraft ID
    'lat': 'Latitude',              # GPS Latitude
    'lon': 'Longitude',             # GPS Longitude
    'alt_baro_ft': 'Baro_Altitude', # Barometric Altitude (feet)
    'gs_knots': 'Velocity',         # Ground Speed (knots)
    'track': 'Heading',             # Flight Heading (degrees)
    'v_rate_fpm': 'Vertical_Rate',  # Climb/Descent Rate (ft/min)
    'rssi': 'Signal_Strength',      # Received Signal Strength (dBFS)
    'rc': 'Message_Rate',           # Integrity / Message Count
    'callsign': 'Callsign'          # Flight Number (e.g. FIN511)
}

# ================= Helper Functions =================

def get_date_from_ns(ns_str):
    """
    Converts a nanosecond timestamp string (e.g., '1764108014000000000') 
    into a readable date string (e.g., '2025-11-26').
    """
    try:
        ts_val = int(ns_str)
        # Convert nanoseconds (19 digits) to seconds (10 digits) if needed
        if len(ns_str) > 10: 
            ts_val = ts_val // 1_000_000_000
        return datetime.datetime.fromtimestamp(ts_val).strftime('%Y-%m-%d')
    except:
        return None

def parse_line(line):
    """
    Parses a single line of InfluxDB Line Protocol.
    Format: measurement,tags fields timestamp
    Example: local_aircraft_state icao24="4aca89",lat=60.3353 1764108014000000000
    """
    try:
        parts = line.strip().split(' ')
        # We need at least Measurement+Fields and Timestamp
        if len(parts) < 2: return None, None, None
        
        # 1. Extract Metadata
        measurement = parts[0].split(',')[0] # Remove tags attached to name
        timestamp_ns = parts[-1]
        
        # 2. Date Filter check
        date_str = get_date_from_ns(timestamp_ns)
        if not date_str or not (START_DATE <= date_str <= END_DATE):
            return None, None, None

        # 3. Data Extraction
        data = {'Timestamp': timestamp_ns}
        
        # Regex Magic: Finds 'key=value' pairs.
        # Handles:
        #  - Quoted strings: callsign="FIN511"
        #  - Integers with suffix: alt_baro_ft=3500i
        #  - Floats: lat=60.3353
        matches = re.findall(r'([a-zA-Z0-9_]+)=(".*?"|[0-9\.\-]+i?)', line)
        
        for key, val in matches:
            # Clean up the value (remove quotes and 'i' suffix)
            val_clean = val.replace('"', '').replace('i', '')
            
            # Map raw field name to clean CSV column name
            if key in FEATURE_MAP:
                data[FEATURE_MAP[key]] = val_clean
            else:
                # Preserve unmapped fields just in case
                data[key] = val_clean
                
        return measurement, data, date_str
        
    except Exception:
        return None, None, None

# ================= Main Execution Flow =================

def main():
    print("="*60)
    print(f" SECURE SKIES: DATA EXTRACTOR (v4.0)")
    print("="*60)
    print(f"[INFO] Input Source:  {INPUT_FILE}")
    print(f"[INFO] Date Window:   {START_DATE} to {END_DATE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Raw dump file '{INPUT_FILE}' not found!")
        print("        Please ensure the .lp file is in this directory.")
        sys.exit(1)

    # 1. Setup CSV Writers
    print("[STEP 1] Initializing Output Files...")
    
    # Define Column Headers (Schema)
    cols_local = ['Timestamp', 'ICAO24', 'Callsign', 'Latitude', 'Longitude', 
                  'Baro_Altitude', 'Velocity', 'Heading', 'Vertical_Rate', 
                  'Signal_Strength', 'Message_Rate']
    
    cols_global = ['Timestamp', 'ICAO24', 'Latitude', 'Longitude', 'Baro_Altitude', 
                   'Velocity', 'Heading', 'Vertical_Rate']
    
    cols_alerts = ['Timestamp', 'Alert_Type', 'Description', 'Raw_Message']

    # Open Files
    try:
        f_local = open(OUT_LOCAL, 'w', newline='')
        f_global = open(OUT_GLOBAL, 'w', newline='')
        f_alerts = open(OUT_ALERTS, 'w', newline='')

        # Create Writers
        w_local = csv.DictWriter(f_local, fieldnames=cols_local, extrasaction='ignore')
        w_global = csv.DictWriter(f_global, fieldnames=cols_global, extrasaction='ignore')
        w_alerts = csv.writer(f_alerts)

        # Write Headers
        w_local.writeheader()
        w_global.writeheader()
        w_alerts.writerow(cols_alerts)
        
    except IOError as e:
        print(f"[ERROR] Could not open output files: {e}")
        sys.exit(1)

    # 2. Process the Dump File
    print("[STEP 2] Processing Raw Data (This may take a moment)...")
    
    stats = {'local': 0, 'global': 0, 'alerts': 0}
    line_count = 0

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line_count += 1
            
            # Progress Indicator (every 1M lines)
            if line_count % 1_000_000 == 0:
                print(f"  > Scanned {line_count // 1_000_000} Million lines...", end='\r')

            # Parse Line
            meas, data, _ = parse_line(line)
            if not meas: continue

            # Route to correct CSV based on Measurement Name
            if meas == 'local_aircraft_state':
                w_local.writerow(data)
                stats['local'] += 1
            
            elif meas == 'global_aircraft_state':
                w_global.writerow(data)
                stats['global'] += 1
            
            elif meas in ['physics_alerts', 'security_alerts', 'runway_events']:
                desc = data.get('message', data.get('description', 'Unknown'))
                w_alerts.writerow([data['Timestamp'], meas, desc, str(data)])
                stats['alerts'] += 1

    # Close Files
    f_local.close()
    f_global.close()
    f_alerts.close()

    # 3. Final Report
    print(f"\n\n[SUCCESS] Extraction Complete!")
    print("-" * 40)
    print(f"  Local Tracks (Input X):   {stats['local']} rows -> {OUT_LOCAL}")
    print(f"  Global Ref (Target Y):    {stats['global']} rows -> {OUT_GLOBAL}")
    print(f"  Verified Alerts:          {stats['alerts']} rows -> {OUT_ALERTS}")
    print("-" * 40)
    print("Action: Share these 3 CSV files with the AI Team.")

if __name__ == "__main__":
    main()
