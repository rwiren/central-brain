import numpy as np
from scipy.optimize import least_squares
import math
import sys

# ==========================================
# 1. CONFIGURATION: YOUR "CORE 4"
# ==========================================
RECEIVERS = {
    "RX1": {"coords": (60.1304, 24.5106, 30.0), "name": "Jorvas (West)"},
    "RX2": {"coords": (60.3196, 24.8295, 50.0), "name": "Keimola (North)"},
    "RX3": {"coords": (60.3760, 25.2710, 40.0), "name": "Sipoo (East)"},
    "RX4": {"coords": (60.1573, 24.9412, 25.0), "name": "Eira (South)"}
}

C = 299792458.0  # Speed of light (m/s)

# ==========================================
# 2. MATH ENGINE
# ==========================================
def lla_to_ecef(lat, lon, alt):
    """Convert Lat/Lon/Alt to Earth-Centered X,Y,Z (meters)."""
    a = 6378137.0           # Earth radius
    f = 1 / 298.257223563   # Flattening
    e2 = 2*f - f**2
    
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    
    N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
    
    x = (N + alt) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (N + alt) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (N * (1 - e2) + alt) * np.sin(lat_rad)
    return np.array([x, y, z])

def ecef_to_lla(x, y, z):
    """Convert X,Y,Z back to Lat/Lon/Alt."""
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2*f - f**2
    
    r = np.sqrt(x**2 + y**2)
    lat = np.arctan2(z, r)
    
    # Iterative refinement for high precision
    for _ in range(5): 
        sin_lat = np.sin(lat)
        N = a / np.sqrt(1 - e2 * sin_lat**2)
        alt = r / np.cos(lat) - N
        lat = np.arctan2(z, r * (1 - e2 * (N / (N + alt))))
        
    lon = np.arctan2(y, x)
    return np.degrees(lat), np.degrees(lon), alt

# Cache Receiver Positions in ECEF
RX_KEYS = list(RECEIVERS.keys())
RX_POSITIONS = []
RX_LATS = []
RX_LONS = []

for k in RX_KEYS:
    lat, lon, alt = RECEIVERS[k]["coords"]
    RX_POSITIONS.append(lla_to_ecef(lat, lon, alt))
    RX_LATS.append(lat)
    RX_LONS.append(lon)
    
RX_POSITIONS = np.array(RX_POSITIONS)

# Calculate Network Centroid (Center point of all sensors)
CENTER_LAT = np.mean(RX_LATS)
CENTER_LON = np.mean(RX_LONS)

def tdoa_error_func(estimated_pos, rx_positions, arrival_times):
    distances = np.linalg.norm(rx_positions - estimated_pos, axis=1)
    calc_travel_times = distances / C
    
    # Compare relative to first receiver
    observed_diffs = arrival_times[1:] - arrival_times[0]
    calc_diffs = calc_travel_times[1:] - calc_travel_times[0]
    
    return calc_diffs - observed_diffs

def solve_position(timestamps_ns):
    t_sec = np.array(timestamps_ns) / 1e9
    
    # --- THE FIX: SMART INITIAL GUESS ---
    # Instead of guessing at ground level (0m), we guess at 10,000m (Cruising Alt).
    # This forces the solver to converge on the positive (Sky) root, not the negative (Earth) root.
    
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
# 3. TEST RUNNER
# ==========================================
if __name__ == "__main__":
    print(f"📡 Core-4 Solver | Center: {CENTER_LAT:.4f}, {CENTER_LON:.4f}")
    
    # 1. Simulate Plane at 30k feet (Positive Altitude)
    target_lla = (60.3000, 24.9500, 9144.0)
    target_ecef = lla_to_ecef(*target_lla)
    
    # 2. Perfect Physics + Noise
    perfect_dists = np.linalg.norm(RX_POSITIONS - target_ecef, axis=1)
    perfect_times_ns = (perfect_dists / C) * 1e9
    noise_ns = np.random.normal(0, 15, 4) # 15ns jitter
    simulated_inputs = perfect_times_ns + noise_ns
    
    print(f"\n✈️  SIMULATION TARGET:  {target_lla}")
    print(f"⏱️  INPUTS (ns):        {simulated_inputs.astype(int)}")
    
    # 3. Solve
    solution = solve_position(simulated_inputs)
    
    if solution:
        lat, lon, alt, cost = solution
        
        # Color Coding for Output
        alt_status = "✅" if alt > 0 else "❌ UNDERGROUND ERROR"
        
        print("-" * 40)
        print(f"🎯 CALCULATED POS:     ({lat:.4f}, {lon:.4f}, {alt:.1f}m) {alt_status}")
        print(f"📉 RESIDUAL COST:      {cost:.5f}")
        
        diff_h = np.linalg.norm(np.array(target_lla[:2]) - np.array([lat, lon])) * 111000
        diff_v = abs(alt - target_lla[2])
        
        print(f"📏 ERROR:              Horiz: {diff_h:.1f}m | Vert: {diff_v:.1f}m")
        
        if diff_h < 100 and diff_v < 150:
             print("\n🟢 STATUS: 3D LOCK CONFIRMED (PHYSICS MATCH)")
        else:
             print("\n🔴 STATUS: MISMATCH / SPOOFING")
    else:
        print("❌ SOLVER FAILED to converge.")
