import time
import os
import requests
import json
import logging
from influxdb import InfluxDBClient
from geopy.distance import geodesic # Used for distance/geofencing checks
import math

# --- CONFIGURATION ---

# Database connection uses standard environment variables
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB = os.getenv('INFLUX_DB', 'readsb')

# GeoJSON Source (Fetches dynamic EFHK coordinates)
GRAFANA_HOST = os.getenv('GRAFANA_HOST', '192.168.1.134')
EFHK_GEOJSON_URL = f"http://{GRAFANA_HOST}:3000/public/gazetteer/airports.geojson"
LOGIC_INTERVAL = 15 # Check every 15 seconds

# Physics Limits (as documented in your Logic-Engines wiki)
VSI_LIMIT_FPM = 6000  # Vertical Rate Limit
MACH_LIMIT = 0.95     # Supersonic/Critical Speed Check (Simplified)

# Global Cache for EFHK Position
EFHK_LAT_LON = None 
LAST_UPDATE_TIME = 0
GEOJSON_CACHE_LIFETIME_MIN = 30 # Only update the coordinate every 30 minutes

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("PhysicsGuard")

# --- HELPER FUNCTIONS ---

def get_efhk_center(url):
    """Fetches and caches the EFHK terminal coordinates from the local GeoJSON."""
    global EFHK_LAT_LON, LAST_UPDATE_TIME
    
    if EFHK_LAT_LON and (time.time() - LAST_UPDATE_TIME) < GEOJSON_CACHE_LIFETIME_MIN * 60:
        return EFHK_LAT_LON
        
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        for feature in response.json().get('features', []):
            if feature.get('properties', {}).get('gps_code') == 'EFHK':
                # GeoJSON coordinates are [longitude, latitude]
                lon, lat = feature['geometry']['coordinates']
                EFHK_LAT_LON = (lat, lon)
                LAST_UPDATE_TIME = time.time()
                logger.info(f"Updated EFHK anchor point: {lat}, {lon}")
                return EFHK_LAT_LON
                
        logger.error("EFHK coordinates not found in GeoJSON payload.")
        return EFHK_LAT_LON # Return stale/default if not found
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch GeoJSON from local endpoint. {e}")
        return EFHK_LAT_LON # Return stale/default if connection fails

def check_kinematics(client, icao, alt_ft, gs_knots, v_rate_fpm):
    """Implements Mach/VSI checks and logs immediate alerts to InfluxDB."""
    
    alerts = []
    
    # 1. VERTICAL RATE CHECK (VSI)
    if abs(v_rate_fpm) > VSI_LIMIT_FPM:
        alerts.append(("VSI_EXCEEDED", v_rate_fpm))
        
    # 2. MACH/SPEED CHECK (Simplified)
    speed_of_sound_kts = 661.47 
    mach_number = gs_knots / speed_of_sound_kts
    if mach_number > MACH_LIMIT:
        alerts.append(("MACH_BREACH", mach_number))
    
    if alerts:
        json_body = [{
            "measurement": "physics_alerts", # New dedicated measurement for physics violations
            "tags": {"icao": icao, "type": alert[0]},
            "fields": {"value": alert[1]}
        } for alert in alerts]
        
        try:
            client.write_points(json_body)
            logger.warning(f"🚨 PHYSICS VIOLATION(S) logged for {icao}.")
        except Exception as e:
            logger.error(f"Failed to log physics alert to DB: {e}")
        return True
    return False

# --- MAIN LOOP ---

def main():
    logger.info("--- PHYSICS GUARD STARTING ---")
    
    # 1. Initialize DB Client
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    client.switch_database(INFLUX_DB)
    
    # 2. Main Processing Loop
    while True:
        start_time = time.time()
        
        # A. Fetch Dynamic Anchor Point (EFHK)
        efhk_pos = get_efhk_center(EFHK_GEOJSON_URL)
        
        # B. Query Local Aircraft Data (Similar to spoof-detector, but focused on kinematics)
        # Fetching data written in the last 15 seconds
        query = f"""
            SELECT last("alt_baro_ft") as alt, last("gs_knots") as speed, last("v_rate_fpm") as vsi, last("lat") as lat, last("lon") as lon 
            FROM "local_aircraft_state" 
            WHERE time > now() - 15s 
            GROUP BY "icao24"
        """
        
        results = client.query(query)
        planes_checked = 0

        for (name, tags), points in results.items():
            planes_checked += 1
            point = list(points)[0]
            icao = tags.get('icao24')
            
            # 1. Kinematic Integrity Check (VSI & Mach)
            check_kinematics(client, 
                             icao, 
                             point.get('alt', 0), 
                             point.get('speed', 0), 
                             point.get('vsi', 0))
            
            # 2. Geofencing Check (Requires Lat/Lon and Anchor)
            if efhk_pos[0] and point.get('lat') and point.get('lon'):
                 # Placeholder for advanced geofence check using geodesic/shapely
                 # check_geofence((point['lat'], point['lon']), efhk_pos)
                 pass

        logger.debug(f"Physics checks completed for {planes_checked} aircraft.")
        
        # C. Control Loop Speed
        time_spent = time.time() - start_time
        wait_time = max(0, LOGIC_INTERVAL - time_spent)
        time.sleep(wait_time)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Physics Guard experienced a fatal error: {e}")
        time.sleep(10) # Wait before exiting container
