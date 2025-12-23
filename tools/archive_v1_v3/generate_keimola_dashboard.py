#!/usr/bin/env python3
"""
Script Name: generate_keimola_dashboard.py
Description: Generates a specialized Grafana Dashboard JSON for the Keimola Grid.
             Visualizes the architectural difference between 'Reference' (RTK)
             and 'Scout' (Standard) nodes.
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     1.0.0
"""

import json
import os

# --- Configuration ---
FILENAME = "keimola_grid.json"
DASHBOARD_TITLE = "Keimola Grid: Reference vs Scout"
DASHBOARD_UID = "keimola_architecture_v1"

def generate_dashboard():
    # Base Structure
    dashboard = {
        "annotations": { "list": [] },
        "editable": True,
        "gnetId": None,
        "graphTooltip": 1, # Shared Crosshair
        "id": None,
        "links": [],
        "panels": [],
        "refresh": "10s",
        "schemaVersion": 36,
        "style": "dark",
        "tags": ["adsb", "keimola", "rtk"],
        "templating": {
            "list": [
                {
                    "current": { "selected": False, "text": "InfluxDB", "value": "InfluxDB" },
                    "hide": 0,
                    "includeAll": False,
                    "label": "Datasource",
                    "multi": False,
                    "name": "DS",
                    "options": [],
                    "query": "influxdb",
                    "refresh": 1,
                    "type": "datasource"
                },
                {
                    "allValue": None,
                    "datasource": { "type": "influxdb", "uid": "${DS}" },
                    "definition": "SHOW TAG VALUES FROM \"system_stats\" WITH KEY = \"host\"",
                    "hide": 0,
                    "includeAll": True,
                    "label": "Nodes",
                    "multi": True,
                    "name": "host",
                    "options": [],
                    "query": "SHOW TAG VALUES FROM \"system_stats\" WITH KEY = \"host\"",
                    "refresh": 1,
                    "sort": 1,
                    "type": "query"
                }
            ]
        },
        "time": { "from": "now-30m", "to": "now" },
        "timezone": "browser",
        "title": DASHBOARD_TITLE,
        "uid": DASHBOARD_UID,
        "version": 1,
        "weekStart": "monday"
    }

    # --- ROW 1: SENSOR HEALTH (RTK vs STANDARD) ---
    
    # Panel 1: GNSS Precision (EPX) - The "Truth" Metric
    panel_precision = {
        "id": 1,
        "gridPos": { "h": 9, "w": 12, "x": 0, "y": 0 },
        "type": "timeseries",
        "title": "📡 GNSS Precision (Horizontal Error)",
        "description": "Comparison of GPS Accuracy. Reference Node (Office) should be < 1.0m. Scout (Balcony) ~3-5m.",
        "datasource": { "type": "influxdb", "uid": "${DS}" },
        "targets": [
            {
                "alias": "$tag_host Error (m)",
                "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
                "measurement": "gpsd_tpv",
                "orderByTime": "ASC",
                "policy": "default",
                "query": "SELECT mean(\"epx\") FROM \"gpsd_tpv\" WHERE (\"host\" =~ /^$host$/) AND $timeFilter GROUP BY time($__interval), \"host\"",
                "refId": "A",
                "resultFormat": "time_series",
                "select": [ [ { "params": ["epx"], "type": "field" }, { "params": [], "type": "mean" } ] ],
                "tags": [ { "key": "host", "operator": "=~", "value": "/^$host$/" } ]
            }
        ],
        "fieldConfig": {
            "defaults": {
                "color": { "mode": "palette-classic" },
                "custom": { "axisLabel": "Error (meters)", "drawStyle": "line", "fillOpacity": 10, "lineWidth": 2, "spanNulls": True },
                "unit": "lengthm",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        { "color": "green", "value": None },
                        { "color": "#EAB839", "value": 1.5 }, # Warn if RTK slips > 1.5m
                        { "color": "red", "value": 5 }        # Bad fix
                    ]
                }
            }
        }
    }
    dashboard["panels"].append(panel_precision)

    # Panel 2: Sky View (Satellites)
    panel_sats = {
        "id": 2,
        "gridPos": { "h": 9, "w": 12, "x": 12, "y": 0 },
        "type": "timeseries",
        "title": "🛰️ Satellite Lock (Sky View)",
        "description": "How many satellites are visible? Balcony should see more than Office.",
        "datasource": { "type": "influxdb", "uid": "${DS}" },
        "targets": [
            {
                "alias": "$tag_host Satellites",
                "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
                "measurement": "gpsd_sky", # Note: Depends on Telegraf 'inputs.gpsd'
                "query": "SELECT mean(\"satellites_used\") FROM \"gpsd_sky\" WHERE (\"host\" =~ /^$host$/) AND $timeFilter GROUP BY time($__interval), \"host\"",
                "refId": "A",
                "select": [ [ { "params": ["satellites_used"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            }
        ],
        "fieldConfig": {
            "defaults": { "unit": "none", "min": 0, "max": 20 }
        }
    }
    dashboard["panels"].append(panel_sats)

    # --- ROW 2: ADS-B PERFORMANCE ---

    # Panel 3: Message Volume
    panel_msgs = {
        "id": 3,
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 9 },
        "type": "timeseries",
        "title": "✈️ ADS-B Message Rate",
        "description": "Traffic volume. Balcony (Scout) should typically see more than Office (Indoor).",
        "datasource": { "type": "influxdb", "uid": "${DS}" },
        "targets": [
            {
                "alias": "$tag_host Msgs/sec",
                "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
                "measurement": "readsb",
                "query": "SELECT mean(\"messages\") FROM \"readsb\" WHERE (\"host\" =~ /^$host$/) AND $timeFilter GROUP BY time($__interval), \"host\"",
                "refId": "A",
                "select": [ [ { "params": ["messages"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            }
        ],
        "fieldConfig": {
            "defaults": { "unit": "pps" }
        }
    }
    dashboard["panels"].append(panel_msgs)

    # Panel 4: Max Range
    panel_range = {
        "id": 4,
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 9 },
        "type": "timeseries",
        "title": "📡 Max Range (Nautical Miles)",
        "datasource": { "type": "influxdb", "uid": "${DS}" },
        "targets": [
            {
                "alias": "$tag_host Range (NM)",
                "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
                "measurement": "readsb",
                "query": "SELECT mean(\"max_distance_in_nautical_miles\") FROM \"readsb\" WHERE (\"host\" =~ /^$host$/) AND $timeFilter GROUP BY time($__interval), \"host\"",
                "refId": "A",
                "select": [ [ { "params": ["max_distance_in_nautical_miles"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            }
        ],
        "fieldConfig": {
            "defaults": { "unit": "lengthnm" }
        }
    }
    dashboard["panels"].append(panel_range)

    # --- ROW 3: HARDWARE HEALTH ---

    # Panel 5: CPU Temp
    panel_temp = {
        "id": 5,
        "gridPos": { "h": 6, "w": 24, "x": 0, "y": 17 },
        "type": "timeseries",
        "title": "🔥 CPU Temperature",
        "datasource": { "type": "influxdb", "uid": "${DS}" },
        "targets": [
            {
                "alias": "$tag_host Temp",
                "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
                "measurement": "system_stats",
                "query": "SELECT mean(\"cpu_temp\") FROM \"system_stats\" WHERE (\"host\" =~ /^$host$/) AND $timeFilter GROUP BY time($__interval), \"host\"",
                "refId": "A",
                "select": [ [ { "params": ["cpu_temp"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            }
        ],
        "fieldConfig": {
            "defaults": { "unit": "celsius", "max": 80 }
        }
    }
    dashboard["panels"].append(panel_temp)

    return dashboard

def main():
    print("========================================================")
    print(f"   DASHBOARD GENERATOR: {DASHBOARD_TITLE}")
    print("========================================================")
    
    try:
        data = generate_dashboard()
        with open(FILENAME, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Generated: {FILENAME}")
        print(f"   Action: Import this file into Grafana.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
