#!/usr/bin/env python3
"""
System: Secure Skies - Training Data Exporter (Extended)
Script: export_training_package_v2.py
Description: Generates the 'Golden Week + Antenna Move' dataset.
             Includes Dec 3rd to capture the indoor-to-outdoor transition.
             Adds RSSI/Signal metrics for quality analysis.

             Target Window: 2025-11-26 to 2025-12-03
"""

import sys
import datetime
import csv
import re

# ================= Configuration =================
INPUT_FILE = 'central_brain_full_dump.lp'
START_DATE = '2025-11-26'
END_DATE   = '2025-12-03'  # Extended to include the antenna move

# Feature Mapping (Raw Influx Name -> Project Column Name)
FEATURE_MAP = {
    'icao24': 'ICAO24',
    'lat': 'Latitude',
    'lon': 'Longitude',
    'alt_baro_ft': 'Baro_Altitude',
    'gs_knots': 'Velocity',
    'track': 'Heading',
    'v_rate_fpm': 'Vertical_Rate',
    'rssi': 'Signal_Strength',  # Critical for seeing the antenna improvement
    'rc': 'Message_Rate',       # Helps quantify "better reception"
    'callsign': 'Callsign'
}

def get_date_from_ns(ns_str):
    try:
        ts_val = int(ns_str)
        if len(ns_str) > 10: ts_val = ts_val // 1_000_000_000
        return datetime.datetime.fromtimestamp(ts_val).strftime('%Y-%m-%d')
    except:
        return None

def parse_line(line):
    try:
        parts = line.strip().split(' ')
        if len(parts) < 3: return None, None, None
        
        measurement = parts[0].split(',')[0]
        timestamp_ns = parts[-1]
        
        date_str = get_date_from_ns(timestamp_ns)
        if not (START_DATE <= date_str <= END_DATE):
            return None, None, None

        data = {}
        data['Timestamp'] = timestamp_ns 
        
        # Regex to grab key=value pairs
        matches = re.findall(r'([a-zA-Z0-9_]+)=(".*?"|[0-9\.\-]+i?)', line)
        
        for key, val in matches:
            val_clean = val.replace('"', '').replace('i', '')
            if key in FEATURE_MAP:
                data[FEATURE_MAP[key]] = val_clean
            else:
                data[key] = val_clean
                
        return measurement, data, date_str
        
    except Exception:
        return None, None, None

def main():
    print(f"[INFO] Exporting Training Package ({START_DATE} to {END_DATE})...")
    
    # File Handlers
    f_local = open('secure_skies_local_v2.csv', 'w', newline='')
    f_global = open('secure_skies_global_v2.csv', 'w', newline='')
    f_alerts = open('secure_skies_alerts_v2.csv', 'w', newline='')

    # Define Columns
    cols_local = ['Timestamp', 'ICAO24', 'Callsign', 'Latitude', 'Longitude', 
                  'Baro_Altitude', 'Velocity', 'Heading', 'Vertical_Rate', 
                  'Signal_Strength', 'Message_Rate'] # Added Signal Metrics
    
    cols_global = ['Timestamp', 'ICAO24', 'Latitude', 'Longitude', 'Baro_Altitude', 
                   'Velocity', 'Heading', 'Vertical_Rate']
    
    cols_alerts = ['Timestamp', 'Alert_Type', 'Description', 'Raw_Message']

    # Writers
    writer_local = csv.DictWriter(f_local, fieldnames=cols_local, extrasaction='ignore')
    writer_global = csv.DictWriter(f_global, fieldnames=cols_global, extrasaction='ignore')
    writer_alerts = csv.writer(f_alerts)

    writer_local.writeheader()
    writer_global.writeheader()
    writer_alerts.writerow(cols_alerts)

    counts = {'local': 0, 'global': 0, 'alerts': 0}
    line_count = 0

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                if line_count % 1_000_000 == 0:
                    print(f"  > Processed {line_count // 1_000_000}M lines...", end='\r')

                meas, data, _ = parse_line(line)
                if not meas: continue

                if meas == 'local_aircraft_state':
                    writer_local.writerow(data)
                    counts['local'] += 1
                
                elif meas == 'global_aircraft_state':
                    writer_global.writerow(data)
                    counts['global'] += 1
                
                elif meas in ['physics_alerts', 'security_alerts', 'runway_events']:
                    alert_type = meas
                    desc = data.get('message', data.get('description', 'Unknown'))
                    raw = str(data)
                    writer_alerts.writerow([data['Timestamp'], alert_type, desc, raw])
                    counts['alerts'] += 1

    except FileNotFoundError:
        print(f"[ERROR] Could not find {INPUT_FILE}")
        sys.exit(1)
    finally:
        f_local.close()
        f_global.close()
        f_alerts.close()

    print(f"\n\n[SUCCESS] Export Complete (v2).")
    print(f"  - Local Tracks:   {counts['local']} rows")
    print(f"  - Global Ref:     {counts['global']} rows")
    print(f"  - Alerts:         {counts['alerts']} rows")
    print("  -> Includes Dec 03 (Antenna Move Event).")

if __name__ == "__main__":
    main()
