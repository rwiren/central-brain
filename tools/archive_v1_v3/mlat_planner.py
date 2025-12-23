import folium
from folium import plugins
import math
import os

# ==========================================
# 1. CONFIGURATION: EDIT YOUR NODES HERE
# ==========================================
target_name = "Helsinki-Vantaa (HEL)"
target_coords = [60.3172, 24.9633]

# The "Core 4" Receivers (West -> North -> East -> South)
receivers = [
    {"id": "RX1", "name": "Jorvas (West)",    "coords": [60.1304, 24.5106], "color": "#e74c3c"}, 
    {"id": "RX2", "name": "Keimola (North)",  "coords": [60.3196, 24.8295], "color": "#3498db"}, 
    {"id": "RX3", "name": "Sipoo (East)",     "coords": [60.3760, 25.2710], "color": "#2ecc71"},
    {"id": "RX4", "name": "Eira (South)",     "coords": [60.1573, 24.9412], "color": "#2c3e50"},
]

# ==========================================
# 2. GEOMETRY ENGINE
# ==========================================
def get_dist(c1, c2):
    """Calculate Haversine distance between two points."""
    R = 6371 # Earth radius in km
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

# ==========================================
# 3. MAP GENERATION
# ==========================================
def generate_map():
    print(f"Generating Network Map for {target_name}...")
    
    m = folium.Map(
        location=[60.25, 24.95],
        zoom_start=10,
        tiles="cartodb positron",
        control_scale=True
    )

    # Draw Target
    folium.Marker(
        location=target_coords,
        icon=folium.Icon(color="gray", icon="plane", prefix="fa"),
        tooltip=f"Target: {target_name}"
    ).add_to(m)

    # Plot Receivers
    for rx in receivers:
        folium.Marker(
            location=rx["coords"],
            tooltip=f"<b>{rx['id']}</b>: {rx['name']}",
            icon=folium.Icon(color="white", icon_color=rx["color"], icon="tower-broadcast", prefix="fa")
        ).add_to(m)

        # Add Text Label
        folium.map.Marker(
            rx["coords"],
            icon=folium.DivIcon(
                icon_size=(150,36),
                icon_anchor=(0,0),
                html=f'<div style="font-size: 10pt; font-weight: bold; color: {rx["color"]}; text-shadow: 1px 1px 0 #fff;">{rx["id"]}</div>'
            )
        ).add_to(m)

    # Draw Logic Box (Sequential)
    link_html = ""
    for i in range(len(receivers)):
        r1 = receivers[i]
        r2 = receivers[(i + 1) % len(receivers)] # Loop back to start
        dist = get_dist(r1["coords"], r2["coords"])
        
        folium.PolyLine(
            [r1["coords"], r2["coords"]],
            color="#27ae60",
            weight=3,
            opacity=0.8,
            dash_array="5, 5"
        ).add_to(m)
        
        link_html += f"<div style='display:flex; justify-content:space-between; font-size:0.8em; border-bottom:1px solid #eee;'><span>{r1['id']} ↔ {r2['id']}</span><b>{dist}km</b></div>"

    # Inject Dashboard
    custom_html = f"""
    <style>
        .panel {{ position: fixed; bottom: 20px; left: 20px; width: 250px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #ccc; font-family: sans-serif; z-index:9999; box-shadow: 0 5px 15px 
rgba(0,0,0,0.1); }}
        h4 {{ margin: 0 0 10px 0; color: #2c3e50; }}
    </style>
    <div class="panel">
        <h4>📡 3D MLAT Configuration</h4>
        <div style="font-size: 0.8em; color: #555; margin-bottom: 10px;">
            <b>The Truth Box:</b><br>
            4 synchronized nodes surrounding the target enable full 3D position verification.
        </div>
        {link_html}
    </div>
    """
    m.get_root().html.add_child(folium.Element(custom_html))

    # Save File
    filename = "mlat_network_map.html"
    m.save(filename)
    print(f"✅ Success! Map saved to: {os.path.abspath(filename)}")

if __name__ == "__main__":
    generate_map()
