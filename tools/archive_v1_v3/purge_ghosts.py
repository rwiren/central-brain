#!/usr/bin/env python3
"""
Script: purge_ghosts.py
Description: 
    Deletes specific invalid 'host' tags from InfluxDB.
    Based on the audit findings.
"""

import requests
import sys

# --- CONFIGURATION ---
INFLUX_HOST = "192.168.1.134"
INFLUX_PORT = 8086
DB_NAME = "readsb"
QUERY_URL = f"http://{INFLUX_HOST}:{INFLUX_PORT}/query"

# The Hit List (Exact names from your audit)
GHOSTS = [
    # Variable Failures
    "${SENSOR_ID:-rpi4-generic}",
    "${SENSOR_ID:-rpi4-next}",
    
    # Old/Dead Names
    "rpi4-adsb",
    "keimola-tower",
    "sensor-bravo",
    "readsb_rpi4",
    "Central-Brain",  # Note the capital letters
    
    # Dead UUIDs
    "5bc9bb5",
    
    # Test/Bug Artifacts
    "simulation",
    "unknown"
]

def delete_host(host):
    print(f"👻 Exorcising host: '{host}'...", end=" ")
    # Escape special characters if needed
    q = f"DELETE WHERE host = '{host}'"
    
    try:
        r = requests.post(QUERY_URL, params={'db': DB_NAME, 'q': q})
        if r.status_code == 200:
            print("✅ GONE")
        else:
            print(f"❌ ERROR: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ FAIL: {e}")

def main():
    print(f"--- GHOSTBUSTER PROTOCOL v1.0 @ {INFLUX_HOST} ---")
    print(f"    Target Database: {DB_NAME}")
    print(f"    Targets: {len(GHOSTS)}")
    print("-" * 50)
    
    for g in GHOSTS:
        print(f"   - {g}")
        
    print("-" * 50)
    confirm = input("Type 'NUKE' to delete all data for these hosts: ")
    
    if confirm == "NUKE":
        print("\n")
        for ghost in GHOSTS:
            delete_host(ghost)
        print("\n✨ Database Cleansed.")
        print("   Run 'python3 tools/check_ghost_hosts.py' to verify.")
    else:
        print("❌ Cancelled.")

if __name__ == "__main__":
    main()
