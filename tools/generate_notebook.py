import json

# This script generates a valid Jupyter Notebook (.ipynb) for your project
# It uses short lines to prevent copy-paste errors.

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 📡 Central Brain: Network Planner\n",
    "\n",
    "Use this tool to visualize your MLAT receiver geometry and the \"Truth Box\". \n",
    "\n",
    "### Instructions\n",
    "1. Run the **Setup** cell to install the map engine.\n",
    "2. Edit the **Configuration** cell with your proposed receiver locations.\n",
    "3. Run the **Generate Map** cell to see the geometry."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# [SETUP] Run this cell first (Shift+Enter)\n",
    "!pip install folium"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# ==========================================\n",
    "# 1. CONFIGURATION: EDIT YOUR NODES HERE\n",
    "# ==========================================\n",
    "# Logic: The \"Core 4\" should surround the target (West -> North -> East -> South)\n",
    "\n",
    "target_name = \"Helsinki-Vantaa (HEL)\"\n",
    "target_coords = [60.3172, 24.9633]\n",
    "\n",
    "receivers = [\n",
    "    {\"id\": \"RX1\", \"name\": \"Jorvas (West)\",    \"coords\": [60.1304, 24.5106], \"color\": \"#e74c3c\"}, \n",
    "    {\"id\": \"RX2\", \"name\": \"Keimola (North)\",  \"coords\": [60.3196, 24.8295], \"color\": \"#3498db\"}, \n",
    "    {\"id\": \"RX3\", \"name\": \"Sipoo (East)\",     \"coords\": [60.3760, 25.2710], \"color\": \"#2ecc71\"},\n",
    "    {\"id\": \"RX4\", \"name\": \"Eira (South)\",     \"coords\": [60.1573, 24.9412], \"color\": \"#2c3e50\"},\n",
    "]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import folium\n",
    "from folium import plugins\n",
    "import math\n",
    "\n",
    "# Helper: Calculate Haversine Distance\n",
    "def get_dist(c1, c2):\n",
    "    R = 6371 # km\n",
    "    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])\n",
    "    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])\n",
    "    dlat, dlon = lat2 - lat1, lon2 - lon1\n",
    "    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2\n",
    "    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))\n",
    "    return round(R * c, 2)\n",
    "\n",
    "# Map Setup\n",
    "m = folium.Map(\n",
    "    location=[60.25, 24.95],\n",
    "    zoom_start=10,\n",
    "    tiles=\"cartodb positron\",\n",
    "    control_scale=True\n",
    ")\n",
    "\n",
    "# Draw Target\n",
    "folium.Marker(\n",
    "    location=target_coords,\n",
    "    icon=folium.Icon(color=\"gray\", icon=\"plane\", prefix=\"fa\"),\n",
    "    tooltip=f\"Target: {target_name}\"\n",
    ").add_to(m)\n",
    "\n",
    "# Plot Receivers\n",
    "for rx in receivers:\n",
    "    folium.Marker(\n",
    "        location=rx[\"coords\"],\n",
    "        tooltip=f\"<b>{rx['id']}</b>: {rx['name']}\",\n",
    "        icon=folium.Icon(color=\"white\", icon_color=rx[\"color\"], icon=\"tower-broadcast\", prefix=\"fa\")\n",
    "    ).add_to(m)\n",
    "\n",
    "    folium.map.Marker(\n",
    "        rx[\"coords\"],\n",
    "        icon=folium.DivIcon(\n",
    "            icon_size=(150,36),\n",
    "            icon_anchor=(0,0),\n",
    "            html=f'<div style=\"font-size: 10pt; font-weight: bold; color: {rx[\"color\"]}; text-shadow: 1px 1px 0 #fff;\">{rx[\"id\"]}</div>'\n",
    "        )\n",
    "    ).add_to(m)\n",
    "\n",
    "# Draw Logic Box (Sequential)\n",
    "link_html = \"\"\n",
    "for i in range(len(receivers)):\n",
    "    r1 = receivers[i]\n",
    "    r2 = receivers[(i + 1) % len(receivers)] # Loop back to start\n",
    "    dist = get_dist(r1[\"coords\"], r2[\"coords\"])\n",
    "    \n",
    "    folium.PolyLine(\n",
    "        [r1[\"coords\"], r2[\"coords\"]],\n",
    "        color=\"#27ae60\",\n",
    "        weight=3,\n",
    "        opacity=0.8,\n",
    "        dash_array=\"5, 5\"\n",
    "    ).add_to(m)\n",
    "    \n",
    "    link_html += f\"<div style='display:flex; justify-content:space-between; font-size:0.8em; border-bottom:1px solid #eee;'><span>{r1['id']} ↔ {r2['id']}</span><b>{dist}km</b></div>\"\n",
    "\n",
    "# Dashboard\n",
    "custom_html = f\"\"\"\n",
    "<style>\n",
    "    .panel {{\n",
    "        position: fixed;\n",
    "        bottom: 20px;\n",
    "        left: 20px;\n",
    "        width: 250px;\n",
    "        background: white;\n",
    "        padding: 15px;\n",
    "        border-radius: 8px;\n",
    "        border: 1px solid #ccc;\n",
    "        font-family: sans-serif;\n",
    "        z-index: 9999;\n",
    "        box-shadow: 0 5px 15px rgba(0,0,0,0.1);\n",
    "    }}\n",
    "    h4 {{ margin: 0 0 10px 0; color: #2c3e50; }}\n",
    "</style>\n",
    "<div class=\"panel\">\n",
    "    <h4>📡 3D MLAT Configuration</h4>\n",
    "    <div style=\"font-size: 0.8em; color: #555; margin-bottom: 10px;\">\n",
    "        <b>The Truth Box:</b><br>\n",
    "        4 synchronized nodes surrounding the target enable full 3D position verification.\n",
    "    </div>\n",
    "    {link_html}\n",
    "</div>\n",
    "\"\"\"\n",
    "m.get_root().html.add_child(folium.Element(custom_html))\n",
    "\n",
    "# Show Map\n",
    "m"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

with open("mlat_planner.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=1)

print("✅ Successfully created mlat_planner.ipynb! Upload this specific file to GitHub.")
