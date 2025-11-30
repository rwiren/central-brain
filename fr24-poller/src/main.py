import os
import time
import json
import requests
import logging
from influxdb import InfluxDBClient

# --- CONFIGURATION ---
# API Settings
FR24_TOKEN = os.getenv('FR24_API_TOKEN', '')
# Bounding Box for Helsinki Area (LatMax, LatMin, LonMin, LonMax)
# Covers roughly 100km around EFHK
BOUNDS = os.getenv('FR24_BOUNDS', '61.0,59.5,23.0,27.0') 
API_URL = "https://fr24api.flightradar24.com/api/live/flight-positions/full"

# InfluxDB Settings (Local on RPi5)
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# Rate Limiting (Explorer Plan = 10 req/min max)
# We use 15s interval = 4 req/min (Safe)
POLL_INTERVAL = 15 

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("FR24-Poller")

def fetch_live_traffic():
    """
    Fetches 'Truth' data from FR24 API.
    Returns a list of aircraft objects.
    """
    headers = {
        "Accept": "application/json",
        "Accept-Version": "v1",
        "Authorization": f"Bearer {FR24_TOKEN}"
    }
    
    params = {
        "bounds": BOUNDS
    }

    try:
        logger.info(f"Polling FR24 API (Bounds: {BOUNDS})...")
        r = requests.get(API_URL, headers=headers, params=params, timeout=5)
        
        if r.status_code == 200:
            data = r.json()
            return data.get('data', [])
        elif r.status_code == 429:
            logger.warning("Rate Limit Exceeded! Cooling down for 60s...")
            time.sleep(60)
        else:
            logger.error(f"API Error {r.status_code}: {r.text}")
            
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        
    return []

def main():
    logger.info("--- FR24 Truth Poller Started ---")
    
    if not FR24_TOKEN:
        logger.error("CRITICAL: FR24_API_TOKEN is missing!")
        return

    # DB Connection
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    while True:
        try:
            client.switch_database(INFLUX_DB)
            logger.info(f"Connected to InfluxDB: {INFLUX_DB}")
            break
        except:
            time.sleep(5)

    # Main Loop
    while True:
        aircraft_list = fetch_live_traffic()
        
        if aircraft_list:
            points = []
            count = 0
            
            for ac in aircraft_list:
                # We only care about identifying the plane and its position source
                # 'source': 'ADSB' (Trusted) or 'MLAT' (Calculated/Jamming Resilient)
                
                points.append({
                    "measurement": "global_aircraft_state",
                    "tags": {
                        "icao": ac.get('hex', 'unknown'),
                        "callsign": ac.get('callsign', 'N/A'),
                        "source": "FR24",
                        "data_source_type": ac.get('source', 'UNKNOWN') # ADSB vs MLAT
                    },
                    "fields": {
                        "lat": float(ac.get('lat', 0)),
                        "lon": float(ac.get('lon', 0)),
                        "alt_ft": int(ac.get('alt', 0)),
                        "speed_kts": int(ac.get('gspeed', 0)),
                        "track": int(ac.get('track', 0)),
                        "squawk": str(ac.get('squawk', '')),
                        "value": 1
                    }
                })
                count += 1

            if points:
                client.write_points(points)
                logger.info(f"Pushed {count} aircraft from FR24 (Credits used: ~{count*2})")
        
        time.sleep(POLL_INTERVAL)
	# Sleep 15s to stay under 10 req/min limit
        #time.sleep(15)

if __name__ == "__main__":
    main()
