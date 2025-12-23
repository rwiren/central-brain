#!/usr/bin/env python3
"""
Script: verify_brain.py
Version: 3.1.0 (Thermals & Hygiene)
Description: 
    Master Health Check for the Central Brain.
    - Audits Sensors (Precision, Sats, Temp).
    - Checks Data Flow.
    - Detects "Ghost" Hosts (Database Pollution).
"""

import requests
import json
import time
from datetime import datetime

# --- CONFIGURATION ---
INFLUX_HOST = "192.168.1.134"
INFLUX_PORT = 8086
DB_NAME = "readsb"

def query_db(q):
    try:
        url = f"http://{INFLUX_HOST}:{INFLUX_PORT}/query"
        params = {'db': DB_NAME, 'q': q}
        r = requests.get(url, params=params, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")
    return None

def print_header(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

def check_sensors():
    print_header("1. SENSOR FLEET VITALS")
    
    # Complex Query: Join Precision (gps_tpv), Sats (gps_data), and Temp (system_stats)
    # We do this in Python to avoid complex Influx joins
    
    hosts_data = {}

    # 1. Get Precision
    q1 = 'SELECT last("epx") as precision FROM "gps_tpv" WHERE time > now() - 5m GROUP BY "host"'
    data = query_db(q1)
    if data and 'series' in data['results'][0]:
        for s in data['results'][0]['series']:
            hosts_data.setdefault(s['tags']['host'], {})['epx'] = s['values'][0][1]

    # 2. Get Satellites
    q2 = 'SELECT last("satellites_used") as sats FROM "gps_data" WHERE time > now() - 5m GROUP BY "host"'
    data = query_db(q2)
    if data and 'series' in data['results'][0]:
        for s in data['results'][0]['series']:
            hosts_data.setdefault(s['tags']['host'], {})['sats'] = s['values'][0][1]

    # 3. Get Temperature
    q3 = 'SELECT last("cpu_temp") as temp FROM "system_stats" WHERE time > now() - 5m GROUP BY "host"'
    data = query_db(q3)
    if data and 'series' in data['results'][0]:
        for s in data['results'][0]['series']:
            hosts_data.setdefault(s['tags']['host'], {})['temp'] = s['values'][0][1]

    if hosts_data:
        print(f"{'NODE':<20} | {'STATUS':<8} | {'SATS':<5} | {'PRECISION':<10} | {'TEMP':<6}")
        print("-" * 65)
        for host, metrics in sorted(hosts_data.items()):
            # Filter unknowns from this view (shown in section 4)
            if host == 'unknown' or '$' in host: continue

            epx = metrics.get('epx', 999)
            sats = metrics.get('sats', 0)
            temp = metrics.get('temp', 0)
            
            status = "🟢 OK"
            if epx > 500: status = "🟡 NOFIX"
            if temp > 70: status = "🔥 HOT"

            epx_str = f"{round(epx, 2)}m" if epx != 999 else "N/A"
            
            print(f"{host:<20} | {status:<8} | {int(sats):<5} | {epx_str:<10} | {temp:.1f}C")
    else:
        print("❌ NO SENSORS DETECTED (Last 5 mins)")

def check_traffic():
    print_header("2. DATA FLOW")
    q = 'SELECT count("lat") FROM "local_aircraft_state" WHERE time > now() - 1m'
    data = query_db(q)
    count = 0
    if data and 'series' in data['results'][0]:
        count = data['results'][0]['series'][0]['values'][0][1]
    
    print(f"✈️  Positions Processed (Last 1m): {count}")
    if count > 0: print("✅ Aggregator is feeding database.")
    else: print("❌ Aggregator appears silent.")

def check_logic():
    print_header("3. INTELLIGENCE STATUS")
    # Battle Engine
    q1 = 'SELECT last("max_range_nm") FROM "rf_battle_stats" WHERE time > now() - 10m'
    res1 = query_db(q1)
    if res1 and 'series' in res1['results'][0]:
        print(f"✅ Battle Engine: ACTIVE")
    else:
        print(f"❌ Battle Engine: INACTIVE")

    # Physics Guard
    q2 = 'SELECT last("value") FROM "physics_alerts" WHERE time > now() - 24h'
    res2 = query_db(q2)
    if res2 and 'series' in res2['results'][0]:
        print(f"✅ Physics Guard: ACTIVE (Alerts found)")
    else:
        print(f"ℹ️  Physics Guard: QUIET (No alerts)")

def check_hygiene():
    print_header("4. DATABASE HYGIENE")
    q = 'SHOW TAG VALUES FROM "gps_tpv" WITH KEY = "host"'
    data = query_db(q)
    
    known_hosts = ['keimola-office', 'keimola-balcony', 'central-brain']
    ghosts = []
    
    if data and 'series' in data['results'][0]:
        for x in data['results'][0]['series'][0]['values']:
            host = x[1]
            if host not in known_hosts:
                ghosts.append(host)
    
    if ghosts:
        print(f"⚠️  GHOST HOSTS DETECTED: {len(ghosts)}")
        for g in ghosts:
            print(f"   👻 {g}")
        print("\n[!] Run 'python3 tools/clean_brain_db.py' to purge these.")
    else:
        print("✅ Database is clean (No ghost hosts).")

def main():
    print(f"--- BRAIN DIAGNOSTIC v3.1 @ {INFLUX_HOST} ---")
    check_sensors()
    check_traffic()
    check_logic()
    check_hygiene()
    print("\n[Done]")

if __name__ == "__main__":
    main()
