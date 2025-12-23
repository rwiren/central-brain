#!/usr/bin/env python3
"""
Script Name: generate_schema_docs.py
Description: Full-Transparency Data Dictionary Generator.
             Crawls InfluxDB and documents EVERY Measurement, Field, and Tag.
             Updated for Level 4 Telemetry (Pilot Intent, Integrity, Weather).
Author:      System Architect (Gemini)
Date:        2025-12-23
Version:     1.4.0 (Level 4 + Santa Support)
"""

import urllib.request
import urllib.parse
import json
import datetime
import re

# --- CONFIGURATION ---
INFLUX_HOST = "192.168.1.134"
PORT = "8086"
DB_NAME = "readsb"
OUTPUT_FILE = "DATASCHEMA.md"

# Comprehensive Field Descriptions
KNOWN_DESCRIPTIONS = {
    # --- LEVEL 4: PILOT INTENT ---
    "nav_altitude_mcp_ft": "Pilot Selected Altitude (MCP) (ft)",
    "nav_heading": "Pilot Selected Heading (deg)",
    "nav_qnh": "Pilot Selected Pressure Setting (hPa)",
    "nav_modes": "Autopilot Modes Active",
    
    # --- LEVEL 4: INTEGRITY & ACCURACY ---
    "nic": "Nav Integrity Category (0-11)",
    "rc": "Radius of Containment (meters)",
    "sil": "Source Integrity Level (0-3)",
    "nac_p": "Nav Accuracy Category (Position)",
    "nac_v": "Nav Accuracy Category (Velocity)",
    "spi": "Special Position Indicator (Ident)",
    "alert": "Flight Status Alert (Squawk change/Emergency)",

    # --- LEVEL 4: PHYSICS ---
    "vert_rate": "Vertical Rate (fpm)",
    "vert_rate_fpm": "Vertical Rate (fpm)",
    "geom_rate_fpm": "Geometric Vertical Rate (fpm)",
    "gs_knots": "Ground Speed (knots)",
    "track": "Ground Track (deg)",
    "baro_rate": "Barometric Vertical Rate (fpm)",
    "tas": "True Airspeed (knots)",
    "mach": "Mach Number",
    "roll": "Roll Angle (deg)",

    # --- WEATHER (METAR) ---
    "temp_c": "Temperature (°C)",
    "temperature_c": "Temperature (°C)",
    "dewpoint_c": "Dew Point (°C)",
    "pressure_hpa": "Barometric Pressure (QNH) (hPa)",
    "wind_dir_deg": "Wind Direction (deg)",
    "wind_speed_kt": "Wind Speed (knots)",
    "visibility_miles": "Visibility (statute miles)",
    "raw_metar": "Raw METAR String",

    # --- AI & ANOMALIES ---
    "is_anomaly": "AI Flag: Anomalous Data point",
    "magic_enabled": "Santa Tracker: Physics Override Active",
    "engine_count": "Detected Engine Count",
    "maneuver": "AI Classified Maneuver (Label)",
    "confidence": "AI Prediction Confidence (0.0-1.0)",
    "drift_km": "GPS vs Reality Drift (km)",

    # --- STANDARD POSITIONING ---
    "lat": "Latitude (deg)",
    "lon": "Longitude (deg)",
    "alt_baro_ft": "Barometric Altitude (ft)",
    "alt_geom_ft": "Geometric (GPS) Altitude (ft)",
    "seen_seconds": "Time since last update (s)",
    
    # --- RF PERFORMANCE ---
    "rssi": "Signal Strength (dBFS)",
    "signal_db": "Signal Strength (dB)",
    "noise_db": "Noise Floor (dB)",
    "messages": "Total Messages Processed",
    "messages_last1min": "Msg Rate (Last 60s)",
    "strong_signals": "Count of Strong Signals (> -3dB)",
    "max_range_meters": "Max Reception Range (m)",
    
    # --- SYSTEM VITALS ---
    "cpu_temp": "CPU Temperature (°C)",
    "cpu_usage": "CPU Load (%)",
    "ram_usage": "RAM Usage (%)",
    "disk_usage": "Disk Usage (%)",
    "uptime": "System Uptime (seconds)"
}

def execute_query(query):
    url = f"http://{INFLUX_HOST}:{PORT}/query?db={DB_NAME}&pretty=true"
    try:
        data = urllib.parse.urlencode({'q': query}).encode('ascii')
        with urllib.request.urlopen(url, data=data, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error executing '{query}': {e}")
        return {}

def get_measurements():
    data = execute_query("SHOW MEASUREMENTS")
    measurements = []
    try:
        for series in data['results'][0]['series']:
            for value in series['values']:
                measurements.append(value[0])
    except:
        pass
    return sorted(measurements)

def describe_measurement(measurement):
    # 1. Get Fields
    fields = []
    f_data = execute_query(f"SHOW FIELD KEYS FROM \"{measurement}\"")
    try:
        for val in f_data['results'][0]['series'][0]['values']:
            key = val[0]
            f_type = val[1]
            
            # Auto-Description Lookups
            desc = KNOWN_DESCRIPTIONS.get(key)
            
            # Heuristics for unknown fields
            if not desc:
                if "inodes" in key: desc = "Filesystem Inodes"
                elif "usage" in key: desc = "Resource Usage Metric"
                elif "count" in key: desc = "Count"
                elif "percent" in key: desc = "Percentage (%)"
                elif "load" in key: desc = "System Load Average"
                else: desc = "Raw Value"
            
            fields.append({"key": key, "type": f_type, "desc": desc})
    except:
        pass

    # 2. Get Tags
    tags = []
    t_data = execute_query(f"SHOW TAG KEYS FROM \"{measurement}\"")
    try:
        for val in t_data['results'][0]['series'][0]['values']:
            key = val[0]
            desc = "Metadata"
            # Specific Tag Descriptions
            if key == "host": desc = "Sensor Identity / Hostname"
            elif key == "icao": desc = "Aircraft Hex ID (Address)"
            elif key == "icao24": desc = "Aircraft Hex ID (24-bit)"
            elif key == "callsign": desc = "Flight Number / Callsign"
            elif key == "role": desc = "Node Role (Anchor/Scout)"
            elif key == "type_code": desc = "Aircraft Type (e.g., B738, SLEI)"
            elif key == "registration": desc = "Tail Number"
            elif key == "station": desc = "Weather Station ID (ICAO)"
            elif key == "maneuver": desc = "AI Training Label (Target Class)"
            
            tags.append({"key": key, "desc": desc})
    except:
        pass
        
    return fields, tags

def generate_markdown(schema):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    md = f"# 📡 Central Brain Data Schema\n"
    md += f"**Generated:** {timestamp}\n"
    md += f"**Database:** `{DB_NAME}`\n"
    md += f"**Host:** `{INFLUX_HOST}`\n\n"
    md += "> **Note:** This schema reflects the *exact* current state of the database. Descriptions are auto-generated based on the Level 4 Ontology.\n\n"
    md += "---\n\n"
    
    # TOC
    md += "## 📑 Table of Contents\n"
    for m in schema:
        name = m['name']
        md += f"- [{name}](#{name})\n"
    md += "\n---\n"

    for m in schema:
        name = m['name']
        md += f"## `{name}`\n"
        
        if m['tags']:
            md += "### 🏷️ Tags (Indexed)\n"
            md += "| Tag Key | Description |\n| :--- | :--- |\n"
            for t in m['tags']:
                md += f"| `{t['key']}` | {t['desc']} |\n"
            md += "\n"
        
        if m['fields']:
            md += "### 🔢 Fields (Metrics)\n"
            md += "| Field Key | Type | Description |\n| :--- | :--- | :--- |\n"
            for f in m['fields']:
                md += f"| `{f['key']}` | `{f['type']}` | {f['desc']} |\n"
        
        md += "\n---\n"
        
    return md

def main():
    print("========================================================")
    print(f"   SCHEMA DOCUMENTATION GENERATOR v1.4.0 (Level 4)")
    print("========================================================")
    
    print("🔍 Scanning Database...")
    tables = get_measurements()
    print(f"   > Found {len(tables)} measurements.")
    
    full_schema = []
    for i, tbl in enumerate(tables):
        print(f"   [{i+1}/{len(tables)}] analyzing {tbl}...")
        fields, tags = describe_measurement(tbl)
        full_schema.append({"name": tbl, "fields": fields, "tags": tags})
        
    print(f"📝 Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        f.write(generate_markdown(full_schema))
        
    print("✅ Done. Open DATASCHEMA.md to see definitions.")

if __name__ == "__main__":
    main()
