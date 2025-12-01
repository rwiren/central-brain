#!/usr/bin/env python3
# ==============================================================================
# FR24 INTELLIGENCE POLLER v1.1
# ==============================================================================
# Description: Fetches premium flight data from FlightRadar24 API.
#              THROTTLED to save credits (runs every 30 mins).
# ==============================================================================

import os
import time
import json
import requests
import logging
from influxdb import InfluxDBClient

__version__ = "1.1.0"

# --- CONFIGURATION ---
FR24_TOKEN = os.getenv('FR24_API_TOKEN', '')
BOUNDS = os.getenv('FR24_BOUNDS', '61.0,59.5,23.0,27.0') 
API_URL = "https://fr24api.flightradar24.com/api/live/flight-positions/full"

INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# Credit Saving Mode: Poll only every 30 minutes (1800s)
POLL_INTERVAL = 1800 

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("FR24-Poller")

def fetch_live_traffic():
    headers = {
        "Accept": "application/json",
        "Accept-Version": "v1",
        "Authorization": f"Bearer {FR24_TOKEN}"
    }
    params = {"bounds": BOUNDS}

    try:
        logger.info(f"Polling FR24 API (Throttled)...")
        r = requests.get(API_URL, headers=headers, params=params, timeout=10)
        
        if r.status_code == 200:
            return r.json().get('data', [])
        elif r.status_code == 429:
            logger.warning("Rate Limit (429). Cooling down...")
            time.sleep(300)
        elif r.status_code == 402:
            logger.error("Payment Required (402). Credits empty. Sleeping 1 hour.")
            time.sleep(3600) 
        else:
            logger.error(f"API Error {r.status_code}: {r.text}")
            
    except Exception as e:
        logger.error(f"Connection failed: {e}")
      
    return []

def main():
    logger.info(f"--- FR24 POLLER v{__version__} STARTED ---")
    
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    while True:
        try:
            client.switch_database(INFLUX_DB)
            break
        except:
            time.sleep(5)

    while True:
        aircraft_list = fetch_live_traffic()
        
        if aircraft_list:
            points = []
            for ac in aircraft_list:
                points.append({
                    "measurement": "global_aircraft_state",
                    "tags": {
                        "icao": ac.get('hex', 'unknown'),
                        "callsign": ac.get('callsign', 'N/A'),
                        "source": "FR24"
                    },
                    "fields": {
                        "lat": float(ac.get('lat', 0)),
                        "lon": float(ac.get('lon', 0)),
                        "alt_ft": int(ac.get('alt', 0)),
                        "squawk": str(ac.get('squawk', '')),
                        "value": 1
                    }
                })

            if points:
                client.write_points(points)
                logger.info(f"Updated {len(points)} targets from FR24.")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
