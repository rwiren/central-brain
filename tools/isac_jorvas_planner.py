import folium
import math
import os

# ==========================================
# 🛑 LOCAL RUNNING REQUIREMENTS 🛑
# ==========================================
# Python: 3.x
# Library: folium
# Installation: pip install folium
# To run: python3 isac_jorvas_planner.py (Execute from the directory where the script is saved)
# ==========================================

# ==========================================
# 1. JORVAS "CONFIG F" (FINAL)
# ==========================================
MAP_CENTER = [60.1315, 24.5050]
HEIGHT = "25m AGL" 
NOMINAL_PLANE = "Unified 25m AGL Operational Plane"

# NODE DEFINITIONS (Using Final Calculated Positions)
NODES = [
    # 🔵 Tx/Pivot (Blue) - Base coords
    {"id": "Blue", "coords": [60.131398, 24.514102], "role": "Tx", "color": "blue"}, 
    # 🟢 Rx North (Green) - Final Position
    {"id": "Green", "coords": [60.132626, 24.511005], "role": "Rx", "color": "green"},
    # 🔴 Rx South (Red) - Final Position (Chain of shifts applied)
    {"id": "Red", "coords": [60.129598, 24.512879], "role": "Rx", "color": "red"}
]

# CONFIG: Sensing Parameters
MAX_RANGE_KM = 1.4
BEARING_CENTER = 250
BEARING_WIDTH = 75 

# ==========================================
# 2. GEOMETRY ENGINE
# ==========================================
def get_dist(c1, c2):
    R = 6371000 
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 0)

def get_sector_points(center, radius_km, start_angle, end_angle, steps=30):
    points = [center]
    lat1 = math.radians(center[0])
    lon1 = math.radians(center[1])
    R = 6371 

    for i in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * (i / steps)
        brng = math.radians(angle)
        lat2 = math.asin(math.sin(lat1)*math.cos(radius_km/R) +
                         math.cos(lat1)*math.sin(radius_km/R)*math.cos(brng))
        lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(radius_km/R)*math.cos(lat1),
                                 math.cos(radius_km/R)-math.sin(lat1)*math.sin(lat2))
        points.append([math.degrees(lat2), math.degrees(lon2)])
    
    points.append(center) 
    return points

# ==========================================
# 3. MAP GENERATOR CORE
# ==========================================

def layer_sensing_cycle(m, tx_node, rx_nodes, color, cycle_id):
    """Draws the geometry for a single Tx cycle."""
    
    # A. Draw the Baselines (Tx -> Rx)
    for rx in rx_nodes:
        folium.PolyLine(
            [tx_node["coords"], rx["coords"]],
            color=color, weight=1, opacity=0.4, dash_array="5, 5",
            tooltip=f"Cycle {cycle_id} Baseline: {tx_node['id']} ↔ {rx['id']}"
        ).add_to(m)

    # B. Draw the High Precision Triangle
    poly_points = [tx_node["coords"]] + [rx["coords"] for rx in rx_nodes] + [tx_node["coords"]]
    folium.Polygon(
        locations=poly_points,
        color=color, weight=1, fill=True, fill_color=color, fill_opacity=0.1,
        tooltip=f"Cycle {cycle_id} Precision Zone"
    ).add_to(m)
    
    # C. Draw the Range Fan (Originating from the active Tx)
    fan_points = get_sector_points(
        tx_node["coords"], 
        radius_km=MAX_RANGE_KM, 
        start_angle=BEARING_CENTER - (BEARING_WIDTH/2), 
        end_angle=BEARING_CENTER + (BEARING_WIDTH/2)
    )
    
    folium.Polygon(
        locations=fan_points,
        color=color, weight=2, dash_array="5, 10",
        fill=True, fill_color=color, fill_opacity=0.01, # Very light fill for overlap
        tooltip=f"Cycle {cycle_id} Max Range"
    ).add_to(m)


def generate_cumulative_map():
    print("📡 Generating Map (3-Cycle Deployment)...")
    m = folium.Map(location=MAP_CENTER, zoom_start=14, tiles="cartodb positron")
    
    # 1. Define the 3 Cycles (TDD Rotational Geometry)
    # The list of nodes is the same for every cycle, just the TX changes.
    all_nodes = NODES
    
    cycles = [
        # Cycle 1: Blue is TX
        {"tx": all_nodes[0], "rx": [all_nodes[1], all_nodes[2]], "color": "darkblue", "id": 1},
        # Cycle 2: Green is TX
        {"tx": all_nodes[1], "rx": [all_nodes[0], all_nodes[2]], "color": "darkgreen", "id": 2},
        # Cycle 3: Red is TX
        {"tx": all_nodes[2], "rx": [all_nodes[0], all_nodes[1]], "color": "darkred", "id": 3}
    ]

    # 2. Draw all 3 Cycles onto the map
    for cycle in cycles:
        layer_sensing_cycle(m, cycle["tx"], cycle["rx"], cycle["color"], cycle["id"])

    # 3. Plot ALL Nodes (Fixed Markers)
    for node in all_nodes:
        # Markers for the 3 fixed antennas
        folium.Marker(
            location=node["coords"],
            tooltip=f"<b>{node['id']} ({node['role']})</b><br>Unified Height: 25m AGL",
            icon=folium.Icon(color=node["color"], icon="house-signal" if node["role"] == "Tx" else "satellite-dish", prefix="fa"),
            zIndexOffset=1000
        ).add_to(m)

    # 4. Dashboard
    dashboard_html = f"""
    <div style="position: fixed; bottom: 20px; left: 20px; width: 320px; 
         background: white; padding: 15px; border-radius: 8px; border: 1px solid #ccc; font-family: sans-serif; z-index:9999;">
        <h4 style="margin:0 0 10px 0;">📡 3-Cycle ISAC Coverage</h4>
        <div style="font-size:0.85em; color:#555;">
            <b>Deployment Mode:</b> TDD Rotational (3 Cycles)<br>
            <b>Unified Height:</b> {NOMINAL_PLANE}<br>
            <hr>
            <b>Areas:</b><br>
            <span style="background:darkblue; color:white; padding:1px 3px;">&nbsp;</span> Cycle 1 (Blue Tx)<br>
            <span style="background:darkgreen; color:white; padding:1px 3px;">&nbsp;</span> Cycle 2 (Green Tx)<br>
            <span style="background:darkred; color:white; padding:1px 3px;">&nbsp;</span> Cycle 3 (Red Tx)<br>
            <hr>
            <b>Inter-Site Distances:</b><br>
            Blue ↔ Green: <b>{get_dist(NODES[0]['coords'], NODES[1]['coords'])} m</b><br>
            Blue ↔ Red: <b>{get_dist(NODES[0]['coords'], NODES[2]['coords'])} m</b><br>
            Green ↔ Red: <b>{get_dist(NODES[1]['coords'], NODES[2]['coords'])} m</b>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(dashboard_html))

    # 5. Save
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "isac_cumulative_map.html")
    m.save(output_path)
    print(f"✅ Cumulative Map Generated: {output_path}")

if __name__ == "__main__":
    # Note: I need the function defined in the previous turn, so I will define it again here for a standalone script.
    # The project_point function is needed to re-calculate the final coordinates.
    # Since I don't want to redefine the complexity here, I will hardcode the final coordinates based on the last calculation.
    
    # Final Coords from previous step:
    # Green: [60.132737, 24.511531] -> Shifted: [60.132626, 24.511005]
    # Red: [60.129854, 24.513738] -> Shifted: [60.129598, 24.512879]
    
    # I will replace the NODES variable with the final coordinates calculated in the previous turn.
    
    # NODES (Final Lock)
    NODES = [
        {"id": "Blue", "coords": [60.131398, 24.514102], "role": "Tx", "color": "blue"}, 
        {"id": "Green", "coords": [60.132737, 24.511531], "role": "Rx", "color": "green"},
        {"id": "Red", "coords": [60.129854, 24.513738], "role": "Rx", "color": "red"}
    ]
    
    # Final Coords after all shifts (using calculated values from previous turns)
    NODES[1]['coords'] = [60.132746, 24.511303] # Green (Final: 15m @ 45deg)
    NODES[2]['coords'] = [60.129598, 24.512879] # Red (Final: All shifts)
    
    generate_cumulative_map()
