import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

# ==========================================
# 1. ISAC CONFIGURATION (Helsinki Grid)
# ==========================================
# 1 Tx Node (Illuminator)
TX_NODE = {"coords": np.array([0, 0]), "name": "Tx1 (Master)"}

# 2 Rx Nodes (Sensors) - 3km Triangle setup
RX_NODES = [
    {"coords": np.array([3000, 0]),    "name": "Rx1"},
    {"coords": np.array([1500, 2598]), "name": "Rx2"} # Equilateral triangle
]

# The Drone (Target)
TARGET_POS = np.array([1500, 800]) # Meters relative to Tx

# Speed of Light
C = 299792458.0 

# ==========================================
# 2. PHYSICS ENGINE (BISTATIC RANGE)
# ==========================================
def calculate_bistatic_range(tx, target, rx):
    """
    Total Path: Tx -> Target -> Rx
    """
    d1 = np.linalg.norm(target - tx) # Path 1
    d2 = np.linalg.norm(rx - target) # Path 2
    return d1 + d2

# ==========================================
# 3. SOLVER (Intersection of Ellipses)
# ==========================================
def isac_error_func(estimated_pos, tx_pos, rx_positions, measured_ranges):
    """
    Error = (Calc_Path_Length) - (Measured_Path_Length)
    """
    errors = []
    for i, rx_pos in enumerate(rx_positions):
        calc_range = np.linalg.norm(estimated_pos - tx_pos) + np.linalg.norm(rx_pos - estimated_pos)
        errors.append(calc_range - measured_ranges[i])
    return errors

# ==========================================
# 4. SIMULATION
# ==========================================
print(f"📡 ISAC CONFIGURATION")
print(f"Tx: {TX_NODE['coords']}")
print(f"Target (Drone): {TARGET_POS}")

# 1. Simulate Measurements (What the hardware sees)
measured_paths = []
rx_positions = []
for rx in RX_NODES:
    total_dist = calculate_bistatic_range(TX_NODE['coords'], TARGET_POS, rx['coords'])
    measured_paths.append(total_dist)
    rx_positions.append(rx['coords'])
    print(f"  -> Reflected Signal at {rx['name']}: Path Length {total_dist:.1f}m")

# 2. Solve Position
initial_guess = np.array([1000, 1000]) # Random guess in the sector
result = least_squares(
    isac_error_func, 
    initial_guess, 
    args=(TX_NODE['coords'], rx_positions, measured_paths)
)

print("-" * 30)
if result.success:
    calc_pos = result.x
    err = np.linalg.norm(calc_pos - TARGET_POS)
    print(f"🎯 DETECTED DRONE: {calc_pos.astype(int)}")
    print(f"📏 ACCURACY:      {err:.4f} meters")
else:
    print("❌ Detection Failed")

# ==========================================
# 5. VISUALIZATION (Plotting the Ellipses)
# ==========================================
# (Matplotlib code would go here to draw the ellipses intersecting)
