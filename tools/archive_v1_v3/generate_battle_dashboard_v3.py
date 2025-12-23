#!/usr/bin/env python3
"""
Script Name: generate_battle_dashboard_v3.py
Description: Generates a "Hardcoded" RF Battle Dashboard.
             Removes all variables to force-render data for Keimola Office vs Balcony.
             Use this to debug "No Data" issues in Grafana.
Author:      System Architect (Gemini)
"""

import json

FILENAME = "rf_battle_dashboard_v3_hardcoded.json"
TITLE = "Keimola Grid: RF Battle (Hardcoded)"
UID = "keimola_rf_battle_v3"

def get_dashboard_json():
    return {
      "annotations": { "list": [] },
      "editable": True,
      "gnetId": None,
      "graphTooltip": 1,
      "id": None,
      "links": [],
      "panels": [
        # --- ROW 1: SCOREBOARD ---
        {
          "collapsed": False,
          "gridPos": { "h": 1, "w": 24, "x": 0, "y": 0 },
          "id": 10,
          "panels": [],
          "title": "🏆 The Scoreboard (Hardcoded)",
          "type": "row"
        },
        # PANEL 1: MAX RANGE
        {
          "datasource": { "type": "influxdb", "uid": "${DS}" },
          "fieldConfig": {
            "defaults": {
              "color": { "mode": "thresholds" },
              "thresholds": { "mode": "absolute", "steps": [ { "color": "green", "value": None } ] }
            }
          },
          "gridPos": { "h": 6, "w": 8, "x": 0, "y": 1 },
          "id": 1,
          "options": { "colorMode": "value", "graphMode": "area", "justifyMode": "auto", "reduceOptions": { "calcs": [ "lastNotNull" ], "fields": "", "values": False } },
          "targets": [
            {
              "alias": "Office Range",
              "groupBy": [ { "params": ["$__interval"], "type": "time" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT last(\"max_range_nm\") FROM \"rf_battle_stats\" WHERE \"host\" = 'keimola-office' AND $timeFilter GROUP BY time($__interval)",
              "refId": "A",
              "resultFormat": "time_series",
              "select": [ [ { "params": ["max_range_nm"], "type": "field" }, { "params": [], "type": "last" } ] ]
            },
            {
              "alias": "Balcony Range",
              "groupBy": [ { "params": ["$__interval"], "type": "time" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT last(\"max_range_nm\") FROM \"rf_battle_stats\" WHERE \"host\" = 'keimola-balcony' AND $timeFilter GROUP BY time($__interval)",
              "refId": "B",
              "resultFormat": "time_series",
              "select": [ [ { "params": ["max_range_nm"], "type": "field" }, { "params": [], "type": "last" } ] ]
            }
          ],
          "title": "📡 Max Range (NM)",
          "type": "stat"
        },
        # PANEL 2: GROUND TRAFFIC
        {
          "datasource": { "type": "influxdb", "uid": "${DS}" },
          "fieldConfig": {
            "defaults": { "color": { "mode": "palette-classic" }, "custom": { "axisLabel": "Count", "drawStyle": "bars", "fillOpacity": 80 }, "unit": "none" }
          },
          "gridPos": { "h": 6, "w": 8, "x": 8, "y": 1 },
          "id": 2,
          "targets": [
            {
              "alias": "Office Ground",
              "groupBy": [ { "params": ["$__interval"], "type": "time" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT last(\"ground_count\") FROM \"rf_battle_stats\" WHERE \"host\" = 'keimola-office' AND $timeFilter GROUP BY time($__interval)",
              "refId": "A",
              "select": [ [ { "params": ["ground_count"], "type": "field" }, { "params": [], "type": "last" } ] ]
            },
            {
              "alias": "Balcony Ground",
              "groupBy": [ { "params": ["$__interval"], "type": "time" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT last(\"ground_count\") FROM \"rf_battle_stats\" WHERE \"host\" = 'keimola-balcony' AND $timeFilter GROUP BY time($__interval)",
              "refId": "B",
              "select": [ [ { "params": ["ground_count"], "type": "field" }, { "params": [], "type": "last" } ] ]
            }
          ],
          "title": "🚜 Ground Traffic",
          "type": "barchart"
        },

        # --- ROW 2: GRAPHS ---
        {
          "collapsed": False,
          "gridPos": { "h": 1, "w": 24, "x": 0, "y": 7 },
          "id": 12,
          "panels": [],
          "title": "📈 Live Comparison",
          "type": "row"
        },
        {
          "datasource": { "type": "influxdb", "uid": "${DS}" },
          "fieldConfig": {
            "defaults": {
              "custom": { "axisLabel": "Range (NM)", "drawStyle": "line", "fillOpacity": 10, "lineWidth": 2 },
              "unit": "lengthnm"
            }
          },
          "gridPos": { "h": 9, "w": 24, "x": 0, "y": 8 },
          "id": 5,
          "targets": [
            {
              "alias": "Office (Ref)",
              "groupBy": [ { "params": ["$__interval"], "type": "time" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT mean(\"max_range_nm\") FROM \"rf_battle_stats\" WHERE \"host\" = 'keimola-office' AND $timeFilter GROUP BY time($__interval)",
              "refId": "A",
              "select": [ [ { "params": ["max_range_nm"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            },
            {
              "alias": "Balcony (Scout)",
              "groupBy": [ { "params": ["$__interval"], "type": "time" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT mean(\"max_range_nm\") FROM \"rf_battle_stats\" WHERE \"host\" = 'keimola-balcony' AND $timeFilter GROUP BY time($__interval)",
              "refId": "B",
              "select": [ [ { "params": ["max_range_nm"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            }
          ],
          "title": "🔭 Max Range History",
          "type": "timeseries"
        }
      ],
      "refresh": "5s",
      "schemaVersion": 36,
      "style": "dark",
      "tags": ["keimola", "battle", "hardcoded"],
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
          }
        ]
      },
      "time": { "from": "now-15m", "to": "now" },
      "title": TITLE,
      "uid": UID,
      "version": 3
    }

if __name__ == "__main__":
    try:
        with open(FILENAME, 'w') as f:
            json.dump(get_dashboard_json(), f, indent=2)
        print(f"✅ Success: {FILENAME} generated.")
        print(f"   Import this file into Grafana. It bypasses variable selection.")
    except Exception as e:
        print(f"❌ Error: {e}")
