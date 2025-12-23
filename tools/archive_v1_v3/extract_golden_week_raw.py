#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System: Secure Skies - Raw Data Slicer
Script: extract_golden_week_raw.py
Description: surgical extraction of the 'Golden Week' (Nov 27 - Dec 03) 
             from the massive full dump. 
             - Supports reading directly from .gz files.
             - Filters by timestamp nanoseconds.
             - Outputs a lightweight .lp file for the team.

Version: 1.0.0
Author: RW (Lead Solution Architect)
Date: 2025-12-18
"""

import sys
import os
import gzip
import datetime

# ================= Configuration =================
# We look for the compressed file first, then the raw file
INPUT_GZ = 'central_brain_full_dump.lp.gz'
INPUT_RAW = 'central_brain_full_dump.lp'

OUTPUT_FILE = 'secure_skies_golden_week_raw.lp'

# Target Window (Inclusive)
START_DATE = "2025-11-27"
END_DATE   = "2025-12-03"

# ================= Logic =================

def get_timestamp_range():
    """Converts string dates to nanosecond integers for fast comparison."""
    # Start of day Nov 27
    dt_start = datetime.datetime.strptime(START_DATE, "%Y-%m-%d")
    ts_start = int(dt_start.timestamp() * 1_000_000_000)
    
    # End of day Dec 03 (23:59:59)
    dt_end = datetime.datetime.strptime(END_DATE, "%Y-%m-%d")
    dt_end = dt_end.replace(hour=23, minute=59, second=59)
    ts_end = int(dt_end.timestamp() * 1_000_000_000)
    
    return ts_start, ts_end

def open_file_stream():
    """Opens either the .gz or the .lp file depending on what exists."""
    if os.path.exists(INPUT_GZ):
        print(f"[INFO] Found compressed file: {INPUT_GZ}")
        return gzip.open(INPUT_GZ, 'rt', encoding='utf-8')
    elif os.path.exists(INPUT_RAW):
        print(f"[INFO] Found raw file: {INPUT_RAW}")
        return open(INPUT_RAW, 'r', encoding='utf-8')
    else:
        print("[ERROR] No input file found (checked .lp and .lp.gz).")
        sys.exit(1)

def main():
    print("="*60)
    print(" SECURE SKIES: GOLDEN WEEK EXTRACTOR")
    print("="*60)
    
    ts_min, ts_max = get_timestamp_range()
    print(f"[CONF] Extraction Window: {START_DATE} to {END_DATE}")
    print(f"       (Nanoseconds: {ts_min} - {ts_max})")

    extracted_count = 0
    scanned_count = 0
    
    try:
        with open_file_stream() as f_in, open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
            print("[INFO] Scanning stream... (this is fast)")
            
            for line in f_in:
                scanned_count += 1
                if scanned_count % 1_000_000 == 0:
                    print(f"  > Scanned {scanned_count // 1_000_000}M lines...", end='\r')

                try:
                    # Influx Line Protocol format: measurement tagset fieldset timestamp
                    # We just need the last part (timestamp)
                    # Splitting from the right is safer and faster
                    parts = line.rsplit(' ', 1)
                    if len(parts) < 2: continue
                    
                    timestamp_str = parts[1].strip()
                    
                    # Fast integer check
                    # Timestamps must be digits
                    if not timestamp_str.isdigit(): continue
                    
                    ts = int(timestamp_str)
                    
                    # The Core Logic: Is it inside our Golden Week?
                    if ts_min <= ts <= ts_max:
                        f_out.write(line)
                        extracted_count += 1
                        
                except ValueError:
                    continue # Skip malformed lines

        print(f"\n\n[SUCCESS] Extraction Complete.")
        print(f"  - Scanned:   {scanned_count:,} lines")
        print(f"  - Extracted: {extracted_count:,} lines (Golden Week)")
        print(f"  - Saved to:  {OUTPUT_FILE}")
        
        # Check size
        size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"  - File Size: {size_mb:.2f} MB")

    except Exception as e:
        print(f"\n[FAIL] An error occurred: {e}")

if __name__ == "__main__":
    main()
