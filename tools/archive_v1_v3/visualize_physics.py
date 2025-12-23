#!/usr/bin/env python3
"""
System: Telemetry Physics Profiler
Script: visualize_physics.py
Description: Generates a 3D Scatter Plot (Lat, Lon, Altitude) and a 
             Physics Distribution Plot (Velocity vs Altitude).
             Helps the AI team visualize the 'Safe Envelope' of flight parameters.
             
             Target Date: 2025-11-30 (The 'Clean' Day)
"""

import sys
import datetime
import matplotlib.pyplot as plt
import re

# ================= Configuration =================
INPUT_FILE = 'central_brain_full_dump.lp'
TARGET_DATE = '2025-11-30'  # Selected based on your Heatmap analysis

def parse_physics_data(line):
    """
    Extracts Velocity, Altitude, and Vertical Rate for physics profiling.
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

        # Regex Extraction
        vel_match = re.search(r'velocity=([0-9\.-]+)', line)
        alt_match = re.search(r'alt_geom=([0-9\.-]+)', line)
        ver_match = re.search(r'ver_rate=([0-9\.-]+)', line)
        icao_match = re.search(r'icao24="?([a-zA-Z0-9]+)"?', line)

        if vel_match and alt_match and icao_match:
            return {
                'vel': float(vel_match.group(1)),
                'alt': float(alt_match.group(1)),
                'v_rate': float(ver_match.group(1)) if ver_match else 0.0,
                'icao': icao_match.group(1)
            }
    except:
        pass
    return None

def main():
    print(f"[INFO] Mining Physics Data for {TARGET_DATE}...")
    
    velocities = []
    altitudes = []
    climb_rates = []
    
    line_count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line_count += 1
            if line_count % 500000 == 0:
                print(f"  > Scanned {line_count // 1000000}M lines...", end='\r')
            
            data = parse_physics_data(line)
            if data:
                # Filter out ground noise (stopped planes)
                if data['vel'] > 10 or data['alt'] > 100:
                    velocities.append(data['vel'])
                    altitudes.append(data['alt'])
                    climb_rates.append(data['v_rate'])

    print(f"\n[INFO] Extracted {len(velocities)} physics data points.")

    if not velocities:
        print("[WARN] No data found. Check TARGET_DATE.")
        sys.exit()

    # --- Plotting ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Plot 1: Velocity vs Altitude (The "Flight Envelope")
    # This shows the physical limits. Anomalies usually appear outside the main cluster.
    sc1 = ax1.scatter(velocities, altitudes, c=climb_rates, cmap='coolwarm', s=2, alpha=0.6)
    ax1.set_title(f'Flight Envelope: Speed vs Altitude ({TARGET_DATE})')
    ax1.set_xlabel('Ground Speed (knots/mps)')
    ax1.set_ylabel('Geometric Altitude (ft/m)')
    ax1.grid(True, linestyle='--', alpha=0.5)
    plt.colorbar(sc1, ax=ax1, label='Vertical Rate (Climb/Descent)')

    # Plot 2: Histogram of Vertical Rates
    # Helps identifying "Ghost Flights" which often have perfect 0 vertical rate (artificial smoothness)
    ax2.hist(climb_rates, bins=50, color='teal', edgecolor='black', alpha=0.7)
    ax2.set_title('Distribution of Vertical Rates (Climb/Descent)')
    ax2.set_xlabel('Vertical Rate')
    ax2.set_ylabel('Frequency')
    ax2.grid(True, axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    output_file = f"physics_profile_{TARGET_DATE}.png"
    plt.savefig(output_file)
    print(f"[SUCCESS] Physics Profile saved to: {output_file}")

if __name__ == "__main__":
    main()
