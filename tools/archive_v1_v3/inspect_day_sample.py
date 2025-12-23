#!/usr/bin/env python3
"""
System: Data Forensics Tool
Script: inspect_day_sample.py
Description: Scans the raw dump for a specific date and prints the first 
             5 raw lines and a list of ALL detected field names.
             Use this to fix variable name mismatches in visualization scripts.
"""

import sys
import datetime
import collections

INPUT_FILE = 'central_brain_full_dump.lp'
TARGET_DATE = '2025-11-30' # The day we know has data

def main():
    print(f"[INFO] Searching for raw data on {TARGET_DATE}...")
    
    found_lines = 0
    field_tally = collections.Counter()
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                # Basic pre-check to save CPU
                if 'local_aircraft_state' not in line:
                    continue

                parts = line.strip().split(' ')
                if len(parts) < 3: continue
                
                # Check Timestamp
                try:
                    ts_str = parts[-1]
                    ts_val = int(ts_str)
                    if len(ts_str) > 10: ts_val = ts_val // 1_000_000_000
                    dt = datetime.datetime.fromtimestamp(ts_val)
                    if dt.strftime('%Y-%m-%d') != TARGET_DATE:
                        continue
                except:
                    continue

                # We found a match!
                found_lines += 1
                
                # 1. Print Raw Sample (First 3 lines only)
                if found_lines <= 3:
                    print(f"\n[SAMPLE RECORD {found_lines}]")
                    print(line.strip()[:200] + "..." if len(line) > 200 else line.strip())

                # 2. Extract Field Names (Heuristic parse)
                # Fields are in the middle: measurement tag,tag field=val,field=val timestamp
                # We assume the middle part is comma-separated key=values
                try:
                    data_section = " ".join(parts[1:-1])
                    items = data_section.split(',')
                    for item in items:
                        if '=' in item:
                            key = item.split('=')[0]
                            field_tally[key] += 1
                except:
                    pass

                if found_lines >= 500: break # Stop after 500 records to be fast

    except FileNotFoundError:
        print("[ERROR] File not found.")
        sys.exit(1)

    if found_lines == 0:
        print(f"[WARN] No records found for {TARGET_DATE}. (Heatmap might be based on different timezone?)")
    else:
        print("\n" + "="*60)
        print(f"SCHEMA REPORT FOR {TARGET_DATE}")
        print("="*60)
        print(f"{'FIELD NAME':<30} | {'OCCURRENCES':<10}")
        print("-" * 45)
        for field, count in field_tally.most_common(20):
            print(f"{field:<30} | {count:<10}")
        print("="*60)
        print("ACTION: Update 'visualize_physics.py' regex to match these field names.")

if __name__ == "__main__":
    main()
