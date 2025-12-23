#!/usr/bin/env python3
"""
Script Name: compare_rf_performance.py
Description: Head-to-Head comparison of RF performance between nodes.
             Analyzes Signal Strength (RSSI) and Max Range.
             Calculates the "Outdoor Advantage" (Balcony - Office).
Author:      System Architect (Gemini)
Date:        2025-12-04
Version:     1.0.0
"""

import urllib.request
import urllib.parse
import json
import sys

# --- Configuration ---
TARGET_HOST = "192.168.1.134"
PORT = "8086"
DB_NAME = "readsb"

# We compare these two specific identities
NODE_A = "keimola-office"  # Indoor (Reference)
NODE_B = "keimola-balcony" # Outdoor (Scout)

def execute_query(query):
    url = f"http://{TARGET_HOST}:{PORT}/query?db={DB_NAME}&pretty=true"
    try:
        data = urllib.parse.urlencode({'q': query}).encode('ascii')
        with urllib.request.urlopen(url, data=data) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def get_metric(measurement, field, host):
    """Fetches the average value of a metric for the last 1 hour."""
    q = f"SELECT mean(\"{field}\") FROM \"{measurement}\" WHERE \"host\" = '{host}' AND time > now() - 1h"
    res = execute_query(q)
    
    if 'results' in res and 'series' in res['results'][0]:
        # Value is usually at index 1 (index 0 is time)
        return res['results'][0]['series'][0]['values'][0][1]
    return None

def main():
    print("========================================================")
    print(f"   RF PERFORMANCE BATTLE: {NODE_A} vs {NODE_B}")
    print("========================================================")
    
    # 1. Fetch RSSI (Signal Strength)
    # Source: 'local_performance' (from readsb_feeder.py) or 'readsb' (native)
    # We try 'local_performance' first as it's from your active Python feeder
    rssi_a = get_metric("local_performance", "signal_db", NODE_A)
    rssi_b = get_metric("local_performance", "signal_db", NODE_B)
    
    # 2. Fetch Max Range
    # Source: 'adsb_stats' or 'readsb'
    range_a = get_metric("readsb", "max_distance_in_nautical_miles", NODE_A)
    range_b = get_metric("readsb", "max_distance_in_nautical_miles", NODE_B)
    
    # Fallback if readsb table is empty (check adsb_stats)
    if range_a is None:
         range_a = get_metric("adsb_stats", "max_range_km", NODE_A)
         range_unit = "km"
    else:
         range_unit = "NM"

    if range_b is None and range_unit == "km":
         range_b = get_metric("adsb_stats", "max_range_km", NODE_B)

    # --- REPORT ---
    
    print(f"\nMETRIC: SIGNAL STRENGTH (RSSI)")
    print(f"   {NODE_A:<20}: {rssi_a if rssi_a else 'N/A'} dB")
    print(f"   {NODE_B:<20}: {rssi_b if rssi_b else 'N/A'} dB")
    
    if rssi_a and rssi_b:
        diff = round(rssi_b - rssi_a, 2)
        winner = NODE_B if diff > 0 else NODE_A
        print(f"   🏆 WINNER: {winner} (+{abs(diff)} dB)")
        if winner == NODE_B:
             print("   ✅ Result: Outdoor antenna is performing better (Expected).")
        else:
             print("   ⚠️ Result: INDOOR antenna is stronger? Check cabling on Balcony!")

    print(f"\nMETRIC: MAX RANGE")
    print(f"   {NODE_A:<20}: {range_a if range_a else 'N/A'} {range_unit}")
    print(f"   {NODE_B:<20}: {range_b if range_b else 'N/A'} {range_unit}")

    if range_a and range_b:
        diff = round(range_b - range_a, 2)
        winner = NODE_B if diff > 0 else NODE_A
        print(f"   🏆 WINNER: {winner} (+{abs(diff)} {range_unit})")

    print("\n========================================================")

if __name__ == "__main__":
    main()
