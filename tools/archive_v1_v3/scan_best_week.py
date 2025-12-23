#!/usr/bin/env python3
"""
System: Telemetry Data Heatmap Generator
Script: scan_best_week.py
Description: Scans a massive InfluxDB Line Protocol (.lp) dump line-by-line.
             Aggregates record counts per Day + Table to find the 'Golden Week'
             for AI training.
"""

import sys
import datetime
import collections

# Update this filename to match your exact .lp file path
INPUT_FILE = 'central_brain_full_dump.lp'

def main():
    print(f"[INFO] Scanning {INPUT_FILE}... this may take a minute.")
    
    # Structure: stats[date_string][table_name] = count
    stats = collections.defaultdict(lambda: collections.defaultdict(int))
    total_lines = 0
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                total_lines += 1
                if total_lines % 500000 == 0:
                    print(f"  > Processed {total_lines // 1000000}M lines...", end='\r')

                parts = line.split(' ')
                if len(parts) < 3:
                    continue
                
                # Influx LP format: measurement tagset fieldset timestamp
                # Timestamp is the last part
                measurement = parts[0].replace(',', ' ').split(' ')[0] # Handle cases with/without tags
                timestamp_str = parts[-1].strip()
                
                try:
                    # Influx timestamps are usually nanoseconds (19 digits)
                    # Convert to seconds
                    ts_val = int(timestamp_str)
                    if len(timestamp_str) > 10: 
                        ts_val = ts_val // 1_000_000_000
                    
                    dt = datetime.datetime.fromtimestamp(ts_val)
                    date_key = dt.strftime('%Y-%m-%d')
                    
                    stats[date_key][measurement] += 1
                except:
                    continue

    except FileNotFoundError:
        print(f"[ERROR] File {INPUT_FILE} not found. Check the name.")
        sys.exit(1)

    print("\n\n" + "="*80)
    print(f"DATA HEATMAP (Records per Day)")
    print("="*80)
    
    # Sort dates
    sorted_dates = sorted(stats.keys())
    
    # Define critical tables for the "AI View"
    key_tables = ['local_aircraft_state', 'global_aircraft_state', 'physics_alerts', 'security_alerts']
    
    # Print Header
    header = f"{'DATE':<12} | {'LOCAL (Inputs)':<15} | {'GLOBAL (Ref)':<15} | {'ALERTS (Targets)':<15}"
    print(header)
    print("-" * len(header))
    
    for d in sorted_dates:
        row = stats[d]
        local = row.get('local_aircraft_state', 0)
        global_ref = row.get('global_aircraft_state', 0)
        # Summing physics and security alerts for a total "Anomaly Score"
        alerts = row.get('physics_alerts', 0) + row.get('security_alerts', 0) + row.get('runway_events', 0)
        
        print(f"{d:<12} | {local:<15,} | {global_ref:<15,} | {alerts:<15,}")
        
    print("="*80)

if __name__ == "__main__":
    main()
