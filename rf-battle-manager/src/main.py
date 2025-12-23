#!/usr/bin/env python3
"""
Component: RF Battle Manager (Central Brain)
Revision: 1.0.1 (2025-12-04)
Author: System Architect (Gemini)
Description: Headless version of the 'Live Battle' script.
             Polls Keimola Nodes -> Calculates Metrics -> Pushes to InfluxDB.
"""

import requests
import time
import math
import os
import sys
import logging
from datetime import datetime

# --- Configuration via Environment Variables ---
# Defaults set to your known Keimola IP addresses
# We use these defaults so it works out-of-the-box on your specific network
OFFICE_URL = os.getenv("NODE_OFFICE_URL", "http://192.168.1.152:8080")
BALCONY_URL = os.getenv("NODE_BALCONY_URL", "http://192.168.1.9:8080")

# Central Brain InfluxDB (Localhost because this container runs ON the Brain)
# Note: In docker-compose, we usually use the service name 'influxdb' or host networking
INFLUX_URL = os.getenv("INFLUX_URL", "http://127.0.0.1:8086/write?db=readsb")

# Reference Coordinates (Keimola)
REF_LAT = 60.3195
REF_LON = 24.8310

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("RF-Battle")

NODES = {
    "OFFICE":  {"url": OFFICE_URL, "host": "keimola-office", "role": "reference"},
    "BALCONY": {"url": BALCONY_URL, "host": "keimola-balcony", "role": "scout"}
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates Nautical Miles between two points."""
    R = 3440.065 # NM
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_node_metrics(name, config):
    """Fetches stats and aircraft lists from a node."""
    result = {
        "status": "OK", "rssi": -99.9, "msgs": 0, 
        "total_ac": 0, "ground_ac": 0, "max_range": 0.0,
        "alt_dist": {"Low": 0, "Mid": 0, "High": 0}
    }
    base_url = config['url']

    # 1. Fetch Hardware Stats
    try:
        r = requests.get(f"{base_url}/data/stats.json", timeout=2)
        if r.status_code == 200:
            d = r.json()
            # Logic to find the best non-zero message count
            block = d.get('last1min', d.get('total', {}))
            local = block.get('local', {})
            
            result['rssi'] = local.get('signal', -99.9)
            
            raw_msgs = block.get('messages', local.get('messages', 0))
            # Convert to per-second if using last1min
            result['msgs'] = int(raw_msgs / 60) if 'last1min' in d else int(raw_msgs)
    except Exception as e:
        result['status'] = f"Stats Fail: {e}"

    # 2. Fetch Aircraft positions
    try:
        r = requests.get(f"{base_url}/data/aircraft.json", timeout=2)
        if r.status_code == 200:
            ac_list = r.json().get('aircraft', [])
            result['total_ac'] = len(ac_list)
            
            max_dist = 0.0
            
            for ac in ac_list:
                # Ground Check
                alt = ac.get('alt_baro')
                if str(alt).lower() == "ground":
                    result['ground_ac'] += 1
                elif isinstance(alt, (int, float)):
                    if alt < 10000: result['alt_dist']['Low'] += 1
                    elif alt < 30000: result['alt_dist']['Mid'] += 1
                    else: result['alt_dist']['High'] += 1

                # Range Calculation
                if 'lat' in ac and 'lon' in ac:
                    dist = haversine_distance(REF_LAT, REF_LON, ac['lat'], ac['lon'])
                    if dist > max_dist:
                        max_dist = dist
            
            result['max_range'] = max_dist
    except Exception as e:
        result['status'] = f"Aircraft Fail: {e}"
        
    return result

def push_metrics(name, config, data):
    """Writes metrics to InfluxDB."""
    if "Fail" in data['status']: 
        return

    timestamp = int(time.time() * 1e9)
    
    # Tags
    tags = f"host={config['host']},role={config['role']}"
    
    # Fields
    fields = [
        f"ground_count={data['ground_ac']}i",
        f"total_count={data['total_ac']}i",
        f"max_range_nm={data['max_range']}",
        f"rssi_db={data['rssi']}",
        f"msg_rate={data['msgs']}i",
        f"alt_low={data['alt_dist']['Low']}i",
        f"alt_mid={data['alt_dist']['Mid']}i",
        f"alt_high={data['alt_dist']['High']}i"
    ]
    
    line = f"rf_battle_stats,{tags} {','.join(fields)} {timestamp}"
    
    try:
        r = requests.post(INFLUX_URL, data=line, timeout=2)
        if r.status_code not in [200, 204]:
            logger.error(f"Influx Write Error {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"Influx Connection Error: {e}")

def main():
    logger.info("--- RF Battle Manager v1.0 Started ---")
    logger.info(f"Target DB: {INFLUX_URL}")
    
    while True:
        # Loop through nodes
        for name, config in NODES.items():
            metrics = get_node_metrics(name, config)
            
            if "Fail" in metrics['status']:
                # Only log errors every now and then to avoid spamming logs
                if int(time.time()) % 60 == 0: 
                    logger.warning(f"{name}: {metrics['status']}")
            else:
                push_metrics(name, config, metrics)
                
        # Wait 5 seconds
        time.sleep(5)

if __name__ == "__main__":
    main()
