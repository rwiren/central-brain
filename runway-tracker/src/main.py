#!/usr/bin/env python3
# ==============================================================================
# RUNWAY TRACKER v3.1.0 (Network Fix)
# ==============================================================================

import time
import os
import logging
import requests
from datetime import datetime
from influxdb import InfluxDBClient
from geopy.distance import geodesic

__version__ = "3.1.0"
__updated__ = "2025-12-05"

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================

# 1. Database Connection (Container-to-Container)
# Default to 'influxdb' service name, not localhost
INFLUX_HOST = os.getenv('INFLUX_HOST', 'influxdb')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# 2. Data Source
SOURCE_MEASUREMENT = "local_aircraft_state"

# 3. Airport Geometry
GAZETTEER_URL = os.getenv('GAZETTEER_URL', 'http://central-brain:80/public/gazetteer/airports.geojson')
TARGET_AIRPORT_CODE = os.getenv('TARGET_AIRPORT', 'EFHK')
DEFAULT_CENTER = (60.3172, 24.9633) 

# 4. Spatial Filters
APPROACH_RADIUS_KM = 15.0   
ALTITUDE_CEILING_FT = 4000  

# 5. Physics Thresholds
CLIMB_THRESH_FPM = 500      
DESCEND_THRESH_FPM = -400   
TAXI_MIN_SPEED = 5          
TAXI_MAX_SPEED = 60         
ROLLING_SPEED = 80          

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("RunwayTracker")

def get_airport_coordinates():
    try:
        logger.info(f"Fetching airport data from {GAZETTEER_URL}...")
        resp = requests.get(GAZETTEER_URL, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                if props.get('gps_code') == TARGET_AIRPORT_CODE:
                    coords = feature['geometry']['coordinates']
                    logger.info(f"✅ Found {TARGET_AIRPORT_CODE}: {coords[1]}, {coords[0]}")
                    return (coords[1], coords[0])
            logger.warning(f"Airport {TARGET_AIRPORT_CODE} not found.")
    except Exception as e:
        logger.warning(f"Gazetteer lookup failed: {e}")
    
    return DEFAULT_CENTER

def get_runway(heading):
    if heading is None: return None
    if 120 <= heading <= 180: return "15" 
    if 300 <= heading <= 360: return "33" 
    if 190 <= heading <= 250: return "22" 
    if 10 <= heading <= 70:   return "04" 
    return "??" 

def main():
    logger.info(f"--- RUNWAY TRACKER v{__version__} STARTED ---")
    airport_center = get_airport_coordinates()
    
    logger.info(f"Connecting to InfluxDB at {INFLUX_HOST}:{INFLUX_PORT}...")
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    while True:
        try:
            client.switch_database(INFLUX_DB)
            logger.info(f"Connected to Database: {INFLUX_DB}")
            break
        except:
            logger.warning("Waiting for InfluxDB...")
            time.sleep(5)

    flight_cache = {}

    while True:
        try:
            now = time.time()
            time_str = datetime.now().strftime("%H:%M:%S")
            flight_cache = {k:v for k,v in flight_cache.items() if now - v['last_seen'] < 300}

            query = f"""
                SELECT last("lat") as lat, last("lon") as lon, 
                       last("alt_baro_ft") as alt, last("gs_knots") as speed, 
                       last("vert_rate") as vsi, last("track") as heading, 
                       last("squawk") as squawk, last("callsign") as callsign
                FROM "{SOURCE_MEASUREMENT}" 
                WHERE time > now() - 15s 
                AND "alt_baro_ft" < {ALTITUDE_CEILING_FT}
                GROUP BY *
            """
            
            try:
                results = client.query(query)
            except Exception as e:
                logger.error(f"Query Failed: {e}")
                time.sleep(5)
                continue
            
            for (name, tags), points in results.items():
                point = list(points)[0]
                icao = tags.get('icao') or tags.get('icao24')
                if not icao: continue
                
                callsign = tags.get('callsign') or point.get('callsign') or icao.upper()
                squawk = point.get('squawk', "----")
                lat = point.get('lat')
                lon = point.get('lon')
                alt = float(point.get('alt') or 0.0)
                speed = float(point.get('speed') or 0.0)
                heading = float(point.get('heading') or 0.0)
                
                if lat is None or lon is None: continue

                dist = geodesic((lat, lon), airport_center).km
                if dist < APPROACH_RADIUS_KM:
                    
                    event_type = None
                    # Logic: Taxi vs Takeoff vs Landing
                    if alt < 100 and speed < 60 and speed > TAXI_MIN_SPEED:
                        event_type = "taxiing"
                    elif float(point.get('vsi') or 0) > CLIMB_THRESH_FPM and speed > 100:
                        event_type = "takeoff"
                    elif float(point.get('vsi') or 0) < DESCEND_THRESH_FPM:
                        event_type = "landing"

                    if event_type:
                        last_event = flight_cache.get(icao, {}).get('last_event')
                        if last_event != event_type:
                            rwy = get_runway(heading)
                            logger.info(f"[{time_str}] ✈️ {event_type.upper()}: {callsign} (RWY {rwy})")
                            
                            json_body = [{
                                "measurement": "runway_events",
                                "tags": { "event": event_type, "runway": rwy },
                                "fields": {
                                    "callsign": str(callsign),
                                    "altitude": float(alt),
                                    "speed": float(speed),
                                    "squawk": str(squawk),
                                    "value": 1.0
                                }
                            }]
                            client.write_points(json_body)
                            
                            flight_cache[icao] = {
                                'last_seen': now, 'last_event': event_type,
                                'runway': rwy, 'callsign': callsign
                            }

        except Exception as e:
            logger.error(f"Loop Error: {e}")
        
        time.sleep(5)

if __name__ == "__main__":
    main()
