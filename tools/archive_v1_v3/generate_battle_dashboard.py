#!/usr/bin/env python3
"""
Script Name: generate_battle_dashboard.py
Description: Generates the official Grafana Dashboard for the Keimola RF Battle.
             Visualizes the 'rf_battle_stats' measurement.
             
             v1.0.1 Fix: Formatted JSON to prevent copy-paste syntax errors.
Author:      System Architect (Gemini)
Date:        2025-12-04
"""

import json

FILENAME = "rf_battle_dashboard.json"
TITLE = "Keimola Grid: RF Battle Command"
UID = "keimola_rf_battle_v1"

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
          "title": "🏆 The Scoreboard (Live)",
          "type": "row"
        },
        # PANEL 1: MAX RANGE
        {
          "datasource": { "type": "influxdb", "uid": "${DS}" },
          "fieldConfig": {
            "defaults": {
              "color": { "mode": "thresholds" },
              "thresholds": {
                "mode": "absolute",
                "steps": [ { "color": "green", "value": None } ]
              }
            }
          },
          "gridPos": { "h": 6, "w": 8, "x": 0, "y": 1 },
          "id": 1,
          "options": { 
              "colorMode": "value", 
              "graphMode": "area", 
              "justifyMode": "auto", 
              "reduceOptions": { "calcs": [ "lastNotNull" ], "fields": "", "values": False }
          },
          "targets": [
            {
              "alias": "$tag_host",
              "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
              "measurement": "rf_battle_stats",
              "orderByTime": "ASC",
              "policy": "default",
              "query": "SELECT last(\"max_range_nm\") FROM \"rf_battle_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"",
              "refId": "A",
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
            "defaults": { 
                "color": { "mode": "palette-classic" }, 
                "custom": { "axisLabel": "Count", "drawStyle": "bars", "fillOpacity": 80 }, 
                "unit": "none" 
            }
          },
          "gridPos": { "h": 6, "w": 8, "x": 8, "y": 1 },
          "id": 2,
          "targets": [
            {
              "alias": "$tag_host Ground",
              "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT last(\"ground_count\") FROM \"rf_battle_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"",
              "refId": "A",
              "select": [ [ { "params": ["ground_count"], "type": "field" }, { "params": [], "type": "last" } ] ]
            }
          ],
          "title": "🚜 Ground Traffic (Airport Hypothesis)",
          "type": "barchart"
        },
        # PANEL 3: MESSAGE RATE
        {
           "datasource": { "type": "influxdb", "uid": "${DS}" },
           "fieldConfig": { "defaults": { "unit": "pps" } },
           "gridPos": { "h": 6, "w": 8, "x": 16, "y": 1 },
           "id": 3,
           "targets": [ 
               { 
                   "alias": "$tag_host", 
                   "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ], 
                   "measurement": "rf_battle_stats", 
                   "query": "SELECT mean(\"msg_rate\") FROM \"rf_battle_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"", 
                   "refId": "A", 
                   "select": [ [ { "params": ["msg_rate"], "type": "field" }, { "params": [], "type": "mean" } ] ] 
               } 
           ],
           "title": "📨 Messages / Sec",
           "type": "stat"
        },

        # --- ROW 2: TACTICAL ANALYSIS ---
        {
          "collapsed": False,
          "gridPos": { "h": 1, "w": 24, "x": 0, "y": 7 },
          "id": 12,
          "panels": [],
          "title": "🔎 Tactical Analysis",
          "type": "row"
        },
        # PANEL 4: SKY SLICE
        {
          "datasource": { "type": "influxdb", "uid": "${DS}" },
          "fieldConfig": {
            "defaults": {
              "custom": { "axisLabel": "Aircraft Count", "drawStyle": "line", "fillOpacity": 40, "stacking": { "group": "A", "mode": "normal" } },
              "unit": "short"
            }
          },
          "gridPos": { "h": 9, "w": 12, "x": 0, "y": 8 },
          "id": 4,
          "targets": [
            {
              "alias": "$tag_host Low (<10k)",
              "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT mean(\"alt_low\") FROM \"rf_battle_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"",
              "refId": "A",
              "select": [ [ { "params": ["alt_low"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            },
            {
              "alias": "$tag_host Mid (10k-30k)",
              "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT mean(\"alt_mid\") FROM \"rf_battle_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"",
              "refId": "B",
              "select": [ [ { "params": ["alt_mid"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            },
            {
              "alias": "$tag_host High (>30k)",
              "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT mean(\"alt_high\") FROM \"rf_battle_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"",
              "refId": "C",
              "select": [ [ { "params": ["alt_high"], "type": "field" }, { "params": [], "type": "mean" } ] ]
            }
          ],
          "title": "🌌 Sky Slice (Altitude Distribution)",
          "type": "timeseries"
        },
        # PANEL 5: MAX RANGE HISTORY
        {
          "datasource": { "type": "influxdb", "uid": "${DS}" },
          "fieldConfig": {
            "defaults": {
              "custom": { "axisLabel": "Range (NM)", "drawStyle": "line", "fillOpacity": 10, "lineWidth": 2 },
              "unit": "lengthnm"
            }
          },
          "gridPos": { "h": 9, "w": 12, "x": 12, "y": 8 },
          "id": 5,
          "targets": [
            {
              "alias": "$tag_host",
              "groupBy": [ { "params": ["$__interval"], "type": "time" }, { "params": ["host"], "type": "tag" } ],
              "measurement": "rf_battle_stats",
              "query": "SELECT mean(\"max_range_nm\") FROM \"rf_battle_stats\" WHERE $timeFilter GROUP BY time($__interval), \"host\"",
              "refId": "A",
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
      "tags": ["keimola", "battle"],
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
      "time": { "from": "now-1h", "to": "now" },
      "title": TITLE,
      "uid": UID,
      "version": 1
    }

if __name__ == "__main__":
    try:
        with open(FILENAME, 'w') as f:
            json.dump(get_dashboard_json(), f, indent=2)
        print(f"✅ Success: {FILENAME} generated.")
        print(f"   Action: Import this file into Grafana.")
    except Exception as e:
        print(f"❌ Error: {e}")
