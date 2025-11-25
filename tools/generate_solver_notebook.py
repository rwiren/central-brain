import json
import numpy as np 
from scipy.optimize import least_squares
import sys
import os 
from typing import List, Dict, Any 
import math 

# ==============================================================================
# 1. DATA BLOCKS (Variables must be outside the function for clean JSON structure)
# ==============================================================================

# Configuration Block (Site Data - AMSL Altitudes)
NODE_CONFIG_CODE = """
RECEIVERS = {
    "RX1": {"coords": (60.1304, 24.5106, 30.0), "name": "Jorvas (Rooftop)"}, 
    "RX2": {"coords": (60.3196, 24.8295, 130.0), "name": "Keimola (11th Floor)"},
    "RX3": {"coords": (60.3760, 25.2710, 60.0), "name": "Sipoo (Rooftop)"}, 
    "RX4": {"coords": (60.1573, 24.9412, 25.0), "name": "Eira (Window)"}
}
"""

# Solver Logic Block
SOLVER_CODE = """
import numpy as np
from scipy.optimize import least_squares
import math

# Speed of Light
C = 299792458.0  

# --- MATH ENGINE (CONVERSION & SOLVER) ---
def lla_to_ecef(lat, lon, alt):
    a = 6378137.0; f = 1 / 298.257223563; e2 = 2*f - f**2
    lat_rad = np.radians(lat); lon_rad = np.radians(lon)
    N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
    x = (N + alt) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (N + alt) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (N * (1 - e2) + alt) * np.sin(lat_rad)
    return np.array([x, y, z])

def ecef_to_lla(x, y, z):
    a = 6378137.0; f = 1 / 298.257223563; e2 = 2*f - f**2
    r = np.sqrt(x**2 + y**2); lat = np.arctan2(z, r)
    for _ in range(5): 
        sin_lat = np.sin(lat)
        N = a / np.sqrt(1 - e2 * sin_lat**2)
        alt = r / np.cos(lat) - N
        lat = np.arctan2(z, r * (1 - e2 * (N / (N + alt))))
    lon = np.arctan2(y, x)
    return np.degrees(lat), np.degrees(lon), alt

# Cache Receiver Positions in ECEF
RX_KEYS = list(RECEIVERS.keys())
RX_POSITIONS = np.array([lla_to_ecef(*RECEIVERS[k]["coords"]) for k in RX_KEYS])
CENTER_LAT = np.mean([RECEIVERS[k]["coords"][0] for k in RX_KEYS])
CENTER_LON = np.mean([RECEIVERS[k]["coords"][1] for k in RX_KEYS])

def tdoa_error_func(estimated_pos, rx_positions, arrival_times):
    distances = np.linalg.norm(rx_positions - estimated_pos, axis=1)
    calc_travel_times = distances / C
    observed_diffs = arrival_times[1:] - arrival_times[0]
    calc_diffs = calc_travel_times[1:] - calc_travel_times[0]
    return calc_diffs - observed_diffs

def solve_mlat(timestamps_ns):
    t_sec = np.array(timestamps_ns) / 1e9
    initial_guess_lla = (CENTER_LAT, CENTER_LON, 10000.0) 
    initial_guess_ecef = lla_to_ecef(*initial_guess_lla)
    
    result = least_squares(
        tdoa_error_func, 
        initial_guess_ecef, 
        args=(RX_POSITIONS, t_sec),
        method='lm'
    )
    if result.success:
        lat, lon, alt = ecef_to_lla(*result.x)
        return lat, lon, alt, result.cost
    return None

# ==========================================
# 3. TEST SIMULATION & OUTPUT
# ==========================================
print(f"📡 Loading Core-4 Configuration: {RX_KEYS}")

target_lla = (60.3172, 24.9633, 9144.0) 
target_ecef = lla_to_ecef(*target_lla)
print(f"✈️  SIMULATION TARGET:  {target_lla}")

perfect_dists = np.linalg.norm(RX_POSITIONS - target_ecef, axis=1)
perfect_times_ns = (perfect_dists / C) * 1e9
noise_ns = np.random.normal(0, 15, 4)
simulated_inputs = perfect_times_ns + noise_ns
print(f"⏱️  Simulated TDoA Jitter: +/- 15ns")

solution = solve_mlat(simulated_inputs)

if solution:
    calc_lat, calc_lon, calc_alt, cost = solution
    diff_h = np.linalg.norm(np.array(target_lla[:2]) - np.array([calc_lat, calc_lon])) * 111000
    diff_v = abs(calc_alt - target_lla[2])
    
    print("\n=== SOLVER DIAGNOSTICS ===")
    print(f"🎯 POSITION (LLA):     ({calc_lat:.4f}, {calc_lon:.4f}, {calc_alt:.1f}m)")
    print(f"📉 RELIABILITY (Cost): {cost:.2e}  <-- Close to zero means perfect intersection.")
    print(f"📏 HORIZ. ERROR:       {diff_h:.1f}m    <-- Positional accuracy on the map.")
    print(f"📏 VERTICAL ERROR:     {diff_v:.1f}m    <-- Altitude accuracy (Z-axis stability).")

    if diff_h < 50 and diff_v < 100:
         print("\n🟢 STATUS: 3D LOCK CONFIRMED (READY FOR LIVE DATA)")
    else:
         print("\n🔴 STATUS: MISMATCH / SPOOFING (Check Geometry or Timing)")
else:
    print("❌ SOLVER FAILED to converge.")
"""

# ==============================================================================
# 3. JSON GENERATION AND FILE WRITE
# ==============================================================================
def generate_final_notebook():
    notebook_content = {
     "cells": [
      {"cell_type": "markdown", 
       "source": ["# 🧮 Central Brain: MLAT Physics Engine\n", 
                  "This tool verifies the stability of your Core-4 Helsinki network geometry using real AMSL altitudes. ",
                  "Click the play button on the cell below to run the test!"]
      },
      {"cell_type": "code", "source": ["!pip install numpy scipy"], "execution_count": None},
      # The main execution cell combining configuration and solver logic
      {"cell_type": "code", "source": [NODE_CONFIG_CODE.strip(), "\n", SOLVER_CODE.strip()], "execution_count": None}
     ],
     "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
     "nbformat": 4, "nbformat_minor": 4
    }

    # --- WRITE THE FILE ---
    try:
        # Use os.path.join to ensure correct path construction
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlat_solver.ipynb")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notebook_content, f, indent=1)
            
        print(f"✅ Successfully created FINAL mlat_solver.ipynb at {output_path}")
    except Exception as e:
        print(f"❌ ERROR WRITING FILE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_final_notebook()
