#!/usr/bin/env python3
# ==============================================================================
# RUNWAY TRACKER v3.0.0
# ==============================================================================
# Author:      RW / Central Brain Project
# Description: Real-time Air Traffic Controller logic.
#              Detects Taxi, Takeoff, Landing, and Aborted Takeoffs.
#              Uses Vector Logic for runway assignment and Dynamic Geofencing.
#
# 📋 CHANGELOG:
#   v2.5: Tag Awareness + Deep Search
#   v2.6: Ground Clamp + Widen Heading
#   v2.7: Removed external dependencies (Self-contained logic)
#   v3.0: (2025-12-01) Added Dynamic Airport Lookup via local GeoJSON gazetteer.
#         Refined comments for all tunable physics parameters.
# ==============================================================================

import time
import os
import logging
import requests
import json
from datetime import datetime
from influxdb import InfluxDBClient
from geopy.distance import geodesic

__version__ = "3.0.0"
__updated__ = "2025-12-01"

# ==========================================
# ⚙️ CONFIGURATION & TUNING
# ==========================================

# 1. Database Connection
# ----------------------
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# 2. Data Source
# 'local_aircraft_state' is the high-frequency feed from the SDR
SOURCE_MEASUREMENT = "local_aircraft_state"

# 3. Airport Geometry (Dynamic)
# ----------------------
# We try to fetch precise coordinates from the local Grafana gazetteer.
# If that fails, we fall back to the hardcoded EFHK center.
GAZETTEER_URL = os.getenv('GAZETTEER_URL', 'http://192.168.1.134:3000/public/gazetteer/airports.geojson')
TARGET_AIRPORT_CODE = os.getenv('TARGET_AIRPORT', 'EFHK')
DEFAULT_CENTER = (60.3172, 24.9633) # EFHK Fallback

# 4. Spatial Filters (The Net)
# ----------------------
# Radius: Distance from airport center to track. 15km covers Final Approach.
APPROACH_RADIUS_KM = 15.0   
# Ceiling: Ignore aircraft above this altitude (e.g., cruising overflights).
ALTITUDE_CEILING_FT = 4000  

# 5. Physics Thresholds (The Logic Engine)
# ----------------------
# Vertical Speed (fpm): Used to distinguish Landing from Takeoff.
CLIMB_THRESH_FPM = 500      # Positive climb > 500 fpm = Takeoff
DESCEND_THRESH_FPM = -400   # Negative climb < -400 fpm = Landing

# Ground Speed (knots): Used to distinguish Taxiing from Rolling.
TAXI_MIN_SPEED = 5          # < 5 kts is considered "Parked" (ignore)
TAXI_MAX_SPEED = 60         # > 60 kts is likely a Takeoff/Landing Roll
ROLLING_SPEED = 80          # > 80 kts means "Committed" (High Energy)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("RunwayTracker")

# --- HELPER: FETCH AIRPORT COORDINATES ---
def get_airport_coordinates():
    """Fetches the target airport coordinates from the local GeoJSON file."""
    try:
        logger.info(f"Fetching airport data from {GAZETTEER_URL}...")
        resp = requests.get(GAZETTEER_URL, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                # Match by ICAO code (e.g. EFHK)
                if props.get('gps_code') == TARGET_AIRPORT_CODE:
                    # GeoJSON is [Lon, Lat], we need (Lat, Lon)
                    coords = feature['geometry']['coordinates']
                    logger.info(f"✅ Found {TARGET_AIRPORT_CODE}: {coords[1]}, {coords[0]}")
                    return (coords[1], coords[0])
            logger.warning(f"Airport {TARGET_AIRPORT_CODE} not found in gazetteer.")
        else:
            logger.warning(f"Gazetteer unreachable (Status {resp.status_code}).")
    except Exception as e:
        logger.warning(f"Gazetteer lookup failed: {e}")
    
    logger.info(f"⚠️ Using default fallback coordinates for {TARGET_AIRPORT_CODE}")
    return DEFAULT_CENTER

# --- HELPER: VECTOR MATH (Heading -> Runway) ---
def get_runway(heading):
    """
    Maps aircraft magnetic heading to EFHK Runway IDs.
    Tolerance is approx +/- 30 degrees to account for crabbing/wind.
    """
    if heading is None: return None
    
    # Runway 15 (South East) / 33 (North West)
    if 120 <= heading <= 180: return "15" 
    if 300 <= heading <= 360: return "33" 
    
    # Runway 22 (South West) / 04 (North East)
    if 190 <= heading <= 250: return "22" 
    if 10 <= heading <= 70:   return "04" 
    
    return "??" 


# ==========================================
# 🚀 MAIN EXECUTION
# ==========================================

def main():
    logger.info(f"--- RUNWAY TRACKER v{__version__} STARTED ---")
    
    # 1. Setup Airport Anchor
    airport_center = get_airport_coordinates()
    
    # 2. Setup DB Connection
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    while True:
        try:
            client.switch_database(INFLUX_DB)
            logger.info(f"Connected to InfluxDB: {INFLUX_DB}")
            break
        except:
            logger.warning("Waiting for InfluxDB...")
            time.sleep(5)

    flight_cache = {}

    while True:
        try:
            now = time.time()
            time_str = datetime.now().strftime("%H:%M:%S")
            
            # Cache Cleanup (Keep planes in memory for 5 mins)
            flight_cache = {k:v for k,v in flight_cache.items() if now - v['last_seen'] < 300}

            # Query Active Traffic
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
            
            results = client.query(query)
            
            for (name, tags), points in results.items():
                point = list(points)[0]
                icao = tags.get('icao') or tags.get('icao24') or tags.get('addr')
                if not icao: continue
                
                # --- METADATA HANDLING ---
                
                # Callsign Logic (Tag -> Field -> Cache -> Hex Fallback)
                callsign = tags.get('callsign') or point.get('callsign')
                if not callsign or callsign == "None":
                    callsign = flight_cache.get(icao, {}).get('callsign')
                if not callsign: callsign = icao.upper()

                # Squawk Logic (Field -> Cache -> Placeholder)
                squawk = point.get('squawk')
                if not squawk or squawk == "0000":
                    squawk = flight_cache.get(icao, {}).get('squawk')
                if not squawk: squawk = "----"

                # --- PHYSICS SANITIZATION ---
                lat = point.get('lat')
                lon = point.get('lon')
                alt = float(point.get('alt') or 0.0)
                raw_vsi = float(point.get('vsi') or 0.0)
                speed = float(point.get('speed') or 0.0)
                heading = float(point.get('heading') or 0.0)
                
                if lat is None or lon is None: continue

                # Calculated VSI (If Transponder reports 0 but altitude is changing)
                calculated_vsi = 0.0
                if icao in flight_cache:
                    prev = flight_cache[icao]
                    time_diff = now - prev['last_seen']
                    alt_diff = alt - prev.get('last_alt', alt)
                    if time_diff > 0: calculated_vsi = (alt_diff / time_diff) * 60

                effective_vsi = raw_vsi
                if raw_vsi == 0 and abs(calculated_vsi) > 100:
                    effective_vsi = calculated_vsi

                # --- GEOMETRY CHECK ---
                dist = geodesic((lat, lon), airport_center).km
                
                if dist < APPROACH_RADIUS_KM:
                    
                    # Debug Log (Proof of Life)
                    logger.info(f"[{time_str}] 👀 {callsign} | Alt:{alt:.0f} | Sqk:{squawk} | Dist:{dist:.1f}km")
                    event_type = None
                    
                    # --- LOGIC ENGINE ---
                    
                    # Priority 1: Ground Clamp (Taxiing)
                    if alt < 100 and speed < 60:
                        if speed > TAXI_MIN_SPEED:
                            event_type = "taxiing"
                        # else: Parked
                    
                    # Priority 2: Takeoff
                    elif effective_vsi > CLIMB_THRESH_FPM and speed > 100:
                        event_type = "takeoff"
                    
                    # Priority 3: Landing
                    elif effective_vsi < DESCEND_THRESH_FPM:
                        event_type = "landing"
                        
                    # Priority 4: Aborted Takeoff
                    elif icao in flight_cache:
                        prev_state = flight_cache[icao]
                        if prev_state.get('rolling_fast', False) and speed < 20 and alt < 500:
                            event_type = "aborted_takeoff"
                            logger.critical(f"[{time_str}] 🚨 ABORTED TAKEOFF: {callsign}")

                    # --- WRITE TO DB ---
                    
                    is_rolling_fast = (speed > ROLLING_SPEED and alt < 500)
                    last_recorded_event = flight_cache.get(icao, {}).get('last_event')
                    
                    if event_type and last_recorded_event != event_type:
                        
                        actual_runway = "GND"
                        if event_type in ["landing", "takeoff"]:
                            rwy = get_runway(heading)
                            if not rwy: rwy = flight_cache.get(icao, {}).get('runway')
                            actual_runway = rwy if rwy else "??"

                        logger.info(f"[{time_str}] ✈️ EVENT: {event_type.upper()} -> {callsign} (RWY {actual_runway})")

                        json_body = [{
                            "measurement": "runway_events",
                            "tags": { "event": event_type, "runway": actual_runway },
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
                            'last_seen': now, 'last_alt': alt,
                            'last_event': event_type, 'rolling_fast': is_rolling_fast,
                            'runway': actual_runway, 'squawk': squawk, 'callsign': callsign
                        }
                    else:
                        prev_runway = flight_cache.get(icao, {}).get('runway')
                        prev_event = flight_cache.get(icao, {}).get('last_event')
                        flight_cache[icao] = {
                            'last_seen': now, 'last_alt': alt,
                            'last_event': event_type if event_type else prev_event,
                            'rolling_fast': is_rolling_fast,
                            'runway': prev_runway, 'squawk': squawk, 'callsign': callsign
                        }

        except Exception as e:
            logger.error(f"Loop Error: {e}")
        
        time.sleep(5)

if __name__ == "__main__":
    main()

# ==========================================
# 🛠️ DEBUGGING GUIDE
# ==========================================
# 1. Check Service Logs:
#    balena device logs <uuid> --service runway-tracker
#
# 2. Verify DB Connection:
#    Look for "Connected to InfluxDB: readsb" on startup.
#
# 3. Verify Airport Location:
#    Look for "✅ Found EFHK: 60.3172, 24.9633" on startup.
