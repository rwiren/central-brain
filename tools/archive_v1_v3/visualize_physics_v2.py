#!/usr/bin/env python3
"""
System: Telemetry Physics Profiler (Corrected Schema)
Script: visualize_physics_v2.py
Description: Generates a Physics Distribution Plot (Speed vs Altitude)
             using the CONFIRMED schema from 2025-11-30.
             
             Corrected Fields:
             - velocity -> gs_knots (Ground Speed)
             - alt_geom -> alt_baro_ft (Barometric Altitude)
             - ver_rate -> v_rate_fpm (Vertical Rate)

Version: 2.0.0
Author: RW
Date: 2025-12-18
"""

import sys
import datetime
import matplotlib.pyplot as plt
import re

# ================= Configuration =================
INPUT_FILE = 'central_brain_full_dump.lp'
TARGET_DATE = '2025-11-30'

def parse_physics_data(line):
    """
    Extracts Speed, Altitude, and Vertical Rate using the VALIDATED schema.
    Handles 'i' integer suffixes from InfluxDB Line Protocol.
    """
    try:
        parts = line.strip().split(' ')
        if len(parts) < 3: return None
        
        measurement = parts[0]
        if measurement != 'local_aircraft_state': return None

        # Parse Timestamp
        ts_str = parts[-1]
        ts_val = int(ts_str)
        if len(ts_str) > 10: ts_val = ts_val // 1_000_000_000
        dt = datetime.datetime.fromtimestamp(ts_val)
        date_str = dt.strftime('%Y-%m-%d')
        
        if date_str != TARGET_DATE: return None

        # Regex Extraction (Updated for actual schema)
        # Matches numbers like: 192.3, 179i, -576i
        
        # gs_knots (Ground Speed)
        speed_match = re.search(r'gs_knots=([0-9\.-]+)(i?)', line)
        
        # alt_baro_ft (Altitude)
        alt_match = re.search(r'alt_baro_ft=([0-9\.-]+)(i?)', line)
        
        # v_rate_fpm (Vertical Rate)
        vr_match = re.search(r'v_rate_fpm=([0-9\.-]+)(i?)', line)
        
        # icao24
        icao_match = re.search(r'icao24="?([a-zA-Z0-9]+)"?', line)

        if speed_match and alt_match and icao_match:
            return {
                'vel': float(speed_match.group(1)),
                'alt': float(alt_match.group(1)),
                'v_rate': float(vr_match.group(1)) if vr_match else 0.0,
                'icao': icao_match.group(1)
            }
    except Exception:
        pass
    return None

def main():
    print(f"[INFO] Mining Physics Data for {TARGET_DATE}...")
    
    velocities = []
    altitudes = []
    climb_rates = []
    
    line_count = 0
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                if line_count % 500000 == 0:
                    print(f"  > Scanned {line_count // 1000000}M lines...", end='\r')
                
                data = parse_physics_data(line)
                if data:
                    # Filter out ground noise (stopped planes or bad data)
                    if data['vel'] > 10 or data['alt'] > 100:
                        velocities.append(data['vel'])
                        altitudes.append(data['alt'])
                        climb_rates.append(data['v_rate'])
                        
    except FileNotFoundError:
        print(f"[ERROR] File {INPUT_FILE} not found.")
        sys.exit(1)

    print(f"\n[INFO] Extracted {len(velocities)} physics data points.")

    if not velocities:
        print("[WARN] No data found. Check date format or file content.")
        sys.exit()

    # --- Plotting ---
    print("[INFO] Generating Plots...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Plot 1: Flight Envelope (Speed vs Altitude)
    sc1 = ax1.scatter(velocities, altitudes, c=climb_rates, cmap='coolwarm', s=2, alpha=0.6)
    ax1.set_title(f'Flight Envelope: Speed vs Altitude ({TARGET_DATE})')
    ax1.set_xlabel('Ground Speed (knots)')
    ax1.set_ylabel('Barometric Altitude (ft)')
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Add colorbar
    cbar = plt.colorbar(sc1, ax=ax1)
    cbar.set_label('Vertical Rate (fpm)')

    # Plot 2: Vertical Rate Distribution
    ax2.hist(climb_rates, bins=50, color='teal', edgecolor='black', alpha=0.7)
    ax2.set_title('Distribution of Vertical Rates (fpm)')
    ax2.set_xlabel('Vertical Rate (ft/min)')
    ax2.set_ylabel('Frequency')
    ax2.grid(True, axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    output_file = f"physics_profile_{TARGET_DATE}.png"
    plt.savefig(output_file, dpi=150)
    print(f"[SUCCESS] Physics Profile saved to: {output_file}")

if __name__ == "__main__":
    main()
