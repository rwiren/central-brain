import time
import os
import logging
from influxdb import InfluxDBClient
from geopy.distance import geodesic

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')
SOURCE_MEASUREMENT = "local_aircraft_state"
AIRPORT_CENTER = (60.3172, 24.9633) 

# Filters & Thresholds
APPROACH_RADIUS_KM = 15.0   
ALTITUDE_CEILING_FT = 4000  
CLIMB_THRESH_FPM = 500      
DESCEND_THRESH_FPM = -400   
TAXI_MIN_SPEED = 5          
TAXI_MAX_SPEED = 40         
ROLLING_SPEED = 80          

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("RunwayTracker")

# --- HELPER: VECTOR MATH ---
def get_runway(heading):
    """Determines EFHK runway based on aircraft heading."""
    if heading is None: return "??"
    
    # Runway 15 (Heading ~150) / 33 (Heading ~330)
    if 130 <= heading <= 170: return "15"
    if 310 <= heading <= 350: return "33"
    
    # Runway 22 (Heading ~220) / 04 (Heading ~040)
    # Covers 22L and 22R
    if 200 <= heading <= 240: return "22"
    if 20 <= heading <= 60:   return "04"
    
    return "??"

def main():
    logger.info(f"--- RUNWAY TRACKER v2.0 (Vector Logic) STARTED ---")
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    while True:
        try:
            client.switch_database(INFLUX_DB)
            break
        except:
            time.sleep(5)

    flight_cache = {}

    while True:
        try:
            now = time.time()
            flight_cache = {k:v for k,v in flight_cache.items() if now - v['last_seen'] < 300}

            # UPDATED QUERY: Added 'track' (Heading)
            query = f"""
                SELECT last("lat") as lat, last("lon") as lon, 
                       last("alt_baro_ft") as alt, last("gs_knots") as speed, 
                       last("vert_rate") as vsi, last("track") as heading, 
                       last("callsign") as callsign
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
                
                lat = point.get('lat')
                lon = point.get('lon')
                alt = float(point.get('alt') or 0.0)
                raw_vsi = float(point.get('vsi') or 0.0)
                speed = float(point.get('speed') or 0.0)
                heading = float(point.get('heading') or 0.0)
                
                callsign = point.get('callsign')
                if not callsign or callsign == "None": callsign = icao.upper()

                if lat is None or lon is None: continue

                # Calculated VSI Fallback
                calculated_vsi = 0.0
                if icao in flight_cache:
                    prev = flight_cache[icao]
                    time_diff = now - prev['last_seen']
                    alt_diff = alt - prev.get('last_alt', alt)
                    if time_diff > 0: calculated_vsi = (alt_diff / time_diff) * 60

                effective_vsi = raw_vsi
                if raw_vsi == 0 and abs(calculated_vsi) > 100:
                    effective_vsi = calculated_vsi

                dist = geodesic((lat, lon), AIRPORT_CENTER).km
                
                if dist < APPROACH_RADIUS_KM:
                    logger.info(f"👀 {callsign} | Alt:{alt:.0f} | Hdg:{heading:.0f}° | Dist:{dist:.1f}km")
                    event_type = None
                    
                    if effective_vsi < DESCEND_THRESH_FPM:
                        event_type = "landing"
                    elif effective_vsi > CLIMB_THRESH_FPM and speed > 100:
                        event_type = "takeoff"
                    elif alt < 500 and speed > TAXI_MIN_SPEED and speed < TAXI_MAX_SPEED:
                        event_type = "taxiing"
                    elif icao in flight_cache:
                        prev_state = flight_cache[icao]
                        if prev_state.get('rolling_fast', False) and speed < 20 and alt < 500:
                            event_type = "aborted_takeoff"
                            logger.critical(f"🚨 ABORTED TAKEOFF: {callsign}")

                    # --- WRITE LOGIC ---
                    is_rolling_fast = (speed > ROLLING_SPEED and alt < 500)
                    last_recorded_event = flight_cache.get(icao, {}).get('last_event')
                    
                    if event_type and last_recorded_event != event_type:
                        # DETERMINISTIC RUNWAY LOGIC
                        if event_type in ["landing", "takeoff"]:
                            actual_runway = get_runway(heading)
                        else:
                            # For taxiing, we keep the previous runway or default
                            actual_runway = flight_cache.get(icao, {}).get('runway', "??")

                        logger.info(f"✈️ {event_type.upper()}: {callsign} on RWY {actual_runway}")

                        json_body = [{
                            "measurement": "runway_events",
                            "tags": { "event": event_type, "runway": actual_runway },
                            "fields": {
                                "callsign": str(callsign),
                                "altitude": float(alt),
                                "speed": float(speed),
                                "squawk": "0000",
                                "value": 1.0
                            }
                        }]
                        client.write_points(json_body)
                        
                        flight_cache[icao] = {
                            'last_seen': now, 'last_alt': alt,
                            'last_event': event_type, 'rolling_fast': is_rolling_fast,
                            'runway': actual_runway
                        }
                    else:
                        prev_runway = flight_cache.get(icao, {}).get('runway')
                        prev_event = flight_cache.get(icao, {}).get('last_event')
                        flight_cache[icao] = {
                            'last_seen': now, 'last_alt': alt,
                            'last_event': event_type if event_type else prev_event,
                            'rolling_fast': is_rolling_fast,
                            'runway': prev_runway
                        }

        except Exception as e:
            logger.error(f"Loop Error: {e}")
        
        time.sleep(5)

if __name__ == "__main__":
    main()
