import requests
import time
import os
import re
from datetime import datetime

# ==============================================================================
# Script: readsb_feeder.py
# Version: 3.0.0 (System Vitals - Stats.json)
# Description: Ingests global performance metrics (Range, Msg Rate, CPU).
# ==============================================================================

NODES = {
    "keimola-office": "http://192.168.1.153:8080",
    "keimola-balcony": "http://192.168.1.9:8080",
    "central-brain": "http://192.168.1.134:8080"
}

INFLUX_HOST = os.getenv("INFLUX_HOST", "http://influxdb:8086")
INFLUX_DB = os.getenv("INFLUX_DB", "readsb")
INFLUX_WRITE_URL = f"{INFLUX_HOST}/write?db={INFLUX_DB}"

MEASUREMENT = "local_performance"

def fetch_stats(base_url):
    try:
        r = requests.get(f"{base_url}/data/stats.json", timeout=2)
        if r.status_code == 200: return r.json()
    except:
        pass
    return None

def main():
    print(f"--- Performance Feeder v3.0.0 Started ---")
    while True:
        lines = []
        for node_name, node_url in NODES.items():
            data = fetch_stats(node_url)
            if not data: continue
            
            # --- 1. GLOBAL COUNTERS ---
            # These are instant snapshots of the tracker state
            ac_with_pos = data.get('aircraft_with_pos', 0)
            ac_no_pos = data.get('aircraft_without_pos', 0)
            
            # --- 2. LAST 1 MINUTE STATS ---
            # Using 'last1min' gives us pre-calculated rates (no derivative needed!)
            l1m = data.get('last1min', {})
            
            # Traffic Volume
            msg_rate = l1m.get('messages', 0)
            pos_rate = l1m.get('position_count_total', 0)
            
            # Range (The most fun stat)
            # Readsb reports this in meters. 
            max_range_m = l1m.get('max_distance', 0)
            
            # Signal Health
            # 'remote' section tells us about data coming from other Pis
            remote = l1m.get('remote', {})
            remote_bytes_in = remote.get('bytes_in', 0)
            
            # CPU Load (ms used by the decoder)
            cpu = l1m.get('cpu', {})
            cpu_load = cpu.get('background', 0) + cpu.get('reader', 0)

            # --- 3. BUILD INFLUX LINE ---
            tags = f"host={node_name},source=ReadsbStats"
            
            fields = [
                f"aircraft_with_pos={ac_with_pos}i",
                f"aircraft_without_pos={ac_no_pos}i",
                f"messages_last1min={msg_rate}i",
                f"positions_last1min={pos_rate}i",
                f"max_range_meters={max_range_m}",
                f"remote_bytes_in={remote_bytes_in}i",
                f"cpu_load_ms={cpu_load}i"
            ]
            
            lines.append(f"{MEASUREMENT},{tags} {','.join(fields)}")

        if lines:
            try:
                requests.post(INFLUX_WRITE_URL, data="\n".join(lines), timeout=2)
            except Exception as e:
                print(f"Write Error: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    main()
