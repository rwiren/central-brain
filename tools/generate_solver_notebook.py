import json

# This script generates 'mlat_solver.ipynb' for your Wiki.
# It packages your physics engine into a format Google Colab can run.

solver_code = r"""
import numpy as np
from scipy.optimize import least_squares
import math

# ==========================================
# 1. CONFIGURATION: YOUR "CORE 4"
# ==========================================
# Coordinates: (Latitude, Longitude, Altitude_meters)
RECEIVERS = {
    "RX1": {"coords": (60.1304, 24.5106, 30.0), "name": "Jorvas (West)"},
    "RX2": {"coords": (60.3196, 24.8295, 50.0), "name": "Keimola (North)"},
    "RX3": {"coords": (60.3760, 25.2710, 40.0), "name": "Sipoo (East)"},
    "RX4": {"coords": (60.1573, 24.9412, 25.0), "name": "Eira (South)"}
}

C = 299792458.0  # Speed of light (m/s)

# ==========================================
# 2. MATH ENGINE (The Physics)
# ==========================================
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
    r = np.sqrt(x**2 + y**2)
    lat = np.arctan2(z, r)
    for _ in range(5): 
        sin_lat = np.sin(lat)
        N = a / np.sqrt(1 - e2 * sin_lat**2)
        alt = r / np.cos(lat) - N
        lat = np.arctan2(z, r * (1 - e2 * (N / (N + alt))))
    lon = np.arctan2(y, x)
    return np.degrees(lat), np.degrees(lon), alt

# Cache Positions
RX_KEYS = list(RECEIVERS.keys())
RX_POSITIONS = np.array([lla_to_ecef(*RECEIVERS[k]["coords"]) for k in RX_KEYS])
CENTER_LAT = np.mean([RECEIVERS[k]["coords"][0] for k in RX_KEYS])
CENTER_LON = np.mean([RECEIVERS[k]["coords"][1] for k in RX_KEYS])

def tdoa_error_func(estimated_pos, rx_positions, arrival_times):
    distances = np.linalg.norm(rx_positions - estimated_pos, axis=1)
    calc_travel_times = distances / C
    return (calc_travel_times[1:] - calc_travel_times[0]) - (arrival_times[1:] - arrival_times[0])

def solve_position(timestamps_ns):
    t_sec = np.array(timestamps_ns) / 1e9
    # Smart Guess: Start at 10,000m to avoid "Underground" mirror solution
    initial_guess_ecef = lla_to_ecef(CENTER_LAT, CENTER_LON, 10000.0) 
    result = least_squares(tdoa_error_func, initial_guess_ecef, args=(RX_POSITIONS, t_sec), method='lm')
    if result.success:
        return (*ecef_to_lla(*result.x), result.cost)
    return None

# ==========================================
# 3. RUN SIMULATION
# ==========================================
print(f"📡 Core-4 Solver Configured: {RX_KEYS}")

# Simulate a plane at 30k feet over Vantaa
target_lla = (60.3000, 24.9500, 9144.0)
target_ecef = lla_to_ecef(*target_lla)

# Physics + Noise
perfect_times_ns = (np.linalg.norm(RX_POSITIONS - target_ecef, axis=1) / C) * 1e9
noise_ns = np.random.normal(0, 15, 4) # 15ns hardware jitter
inputs = perfect_times_ns + noise_ns

print(f"✈️  Target: {target_lla}")
print(f"⏱️  Inputs: {inputs.astype(int)}")

solution = solve_position(inputs)

if solution:
    lat, lon, alt, cost = solution
    status = "✅ 3D LOCK" if (abs(alt - 9144) < 150) else "🔴 SPOOFING ALERT"
    print("-" * 40)
    print(f"🎯 RESULT: ({lat:.4f}, {lon:.4f}, {alt:.1f}m)")
    print(f"📊 STATUS: {status}")
else:
    print("❌ Failed to solve.")
"""

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 🧮 Central Brain: MLAT Physics Engine\n",
    "\n",
    "This tool simulates the mathematical core of the project. It uses the **Levenberg-Marquardt** algorithm to solve the intersection of 4 hyperboloids in 3D space.\n",
    "\n",
    "### Instructions\n",
    "1. Run the **Setup** cell to install Scipy/Numpy.\n",
    "2. Run the **Solver** cell to simulate a plane and see if the math can find it."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# [SETUP] Install Math Libraries\n",
    "!pip install numpy scipy"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": solver_code.splitlines(True) # Split correctly for JSON
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

with open("mlat_solver.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=1)

print("✅ Created mlat_solver.ipynb")
