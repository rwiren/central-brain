#!/usr/bin/env python3
"""
Script: check_ghost_hosts.py
Description: 
    Scans every measurement in InfluxDB for the 'host' tag.
    Flags any host that is NOT in the official fleet list.
"""

import requests
import sys

# --- CONFIGURATION ---
INFLUX_HOST = "192.168.1.134"
INFLUX_PORT = 8086
DB_NAME = "readsb"
QUERY_URL = f"http://{INFLUX_HOST}:{INFLUX_PORT}/query"

# The only 3 devices that should exist
ALLOWED_HOSTS = ["keimola-office", "keimola-balcony", "central-brain"]

def get_measurements():
    try:
        r = requests.get(QUERY_URL, params={'db': DB_NAME, 'q': "SHOW MEASUREMENTS"})
        data = r.json()
        if 'results' in data and 'series' in data['results'][0]:
            return [x[0] for x in data['results'][0]['series'][0]['values']]
    except Exception as e:
        print(f"❌ Error fetching measurements: {e}")
    return []

def check_hosts(measurement):
    q = f'SHOW TAG VALUES FROM "{measurement}" WITH KEY = "host"'
    try:
        r = requests.get(QUERY_URL, params={'db': DB_NAME, 'q': q})
        data = r.json()
        if 'results' in data and 'series' in data['results'][0]:
            all_hosts = [x[1] for x in data['results'][0]['series'][0]['values']]
            ghosts = [h for h in all_hosts if h not in ALLOWED_HOSTS]
            valid = [h for h in all_hosts if h in ALLOWED_HOSTS]
            return ghosts, valid
    except:
        pass
    return [], []

def main():
    print(f"--- DATABASE IDENTITY AUDIT ---")
    print(f"    Target: {INFLUX_HOST}")
    print(f"    Allowed Fleet: {ALLOWED_HOSTS}")
    print("-" * 60)
    
    measurements = get_measurements()
    ghost_found = False
    
    for m in measurements:
        ghosts, valid = check_hosts(m)
        
        if ghosts:
            ghost_found = True
            print(f"Measurement: {m}")
            print(f"  ❌ GHOSTS: {ghosts}")
            if valid:
                print(f"  ✅ Valid:  {valid}")
            print("-" * 60)
            
    if not ghost_found:
        print("✅ CLEAN: No ghost hosts found in any table.")
    else:
        print("\nTo purge a ghost, run this in your brain terminal:")
        print("influx -database readsb -execute \"DELETE WHERE host = 'GHOST_NAME'\"")

if __name__ == "__main__":
    main()
