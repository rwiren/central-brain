import folium
from folium import plugins
import math

# ==========================================
# 1. ISAC CONFIGURATION (Edit this!)
# ==========================================
# Scenario: A 3km Triangle in Vantaa
TX_NODE = {"name": "Tx Master (High Site)", "coords": [60.2941, 25.0409], "color": "red"} # e.g., Water Tower
RX_NODES = [
    {"name": "Rx1 (Sensor A)", "coords": [60.3155, 25.0064], "color": "blue"}, # ~3km NW
    {"name": "Rx2 (Sensor B)", "coords": [60.2800, 24.9800], "color": "blue"}  # ~3km SW
]

# ==========================================
# 2. GEOMETRY ENGINE
# ==========================================
def get_dist(c1, c2):
    """Haversine distance in km"""
    R = 6371 
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

# ==========================================
# 3. MAP GENERATOR
# ==========================================
m = folium.Map(
    location=[60.295, 25.01], # Center of the triangle
    zoom_start=12,
    tiles="cartodb positron"
)

# A. Plot Tx (The Illuminator)
folium.Marker(
    location=TX_NODE["coords"],
    tooltip=f"<b>{TX_NODE['name']}</b><br>Active Illuminator",
    icon=folium.Icon(color="red", icon="wifi", prefix="fa"),
    zIndexOffset=1000
).add_to(m)

# Circle showing immediate "Direct Signal" blast radius (usually a blind spot)
folium.Circle(
    location=TX_NODE["coords"],
    radius=500, # 500m blind zone
    color="red", weight=1, fill=True, fill_opacity=0.1,
    tooltip="Direct Path Interference Zone"
).add_to(m)

# B. Plot Rx Nodes (The Sensors)
rx_coords = []
for rx in RX_NODES:
    rx_coords.append(rx["coords"])
    
    # Marker
    folium.Marker(
        location=rx["coords"],
        tooltip=f"<b>{rx['name']}</b><br>Passive Sensor",
        icon=folium.Icon(color="blue", icon="ear-listen", prefix="fa")
    ).add_to(m)

    # Baseline Line (Tx -> Rx)
    # This is critical. If a drone is on this line, you cannot detect range (Forward Scatter).
    dist = get_dist(TX_NODE["coords"], rx["coords"])
    folium.PolyLine(
        [TX_NODE["coords"], rx["coords"]],
        color="orange", weight=2, dash_array="5, 10",
        tooltip=f"Baseline: {dist}km"
    ).add_to(m)

# C. The "Sensing Triangle" (Area of highest precision)
# Polygon connecting Tx -> Rx1 -> Rx2 -> Tx
poly_points = [TX_NODE["coords"]] + rx_coords + [TX_NODE["coords"]]

folium.Polygon(
    locations=poly_points,
    color="green", weight=0, fill=True, fill_opacity=0.1,
    tooltip="Optimal Sensing Area (Bistatic Triangle)"
).add_to(m)

# D. Dashboard
dashboard_html = """
<div style="position: fixed; bottom: 20px; left: 20px; width: 280px; 
     background: white; padding: 15px; border-radius: 8px; border: 1px solid #ccc; font-family: sans-serif; z-index:9999;">
    <h4 style="margin:0 0 10px 0;">📡 ISAC Deployment</h4>
    <div style="font-size:0.85em; color:#555;">
        <b>Tx (Red):</b> Active Illuminator<br>
        <b>Rx (Blue):</b> Passive Receivers<br>
        <hr>
        <span style="color:orange">---</span> <b>Baselines:</b> High interference zone.<br>
        <span style="background:#e8f5e9; padding:0 3px;">Green</span> <b>Triangle:</b> Best detection accuracy.
    </div>
</div>
"""
m.get_root().html.add_child(folium.Element(dashboard_html))

filename = "isac_deployment_map.html"
m.save(filename)
print(f"✅ ISAC Map Generated: {filename}")
