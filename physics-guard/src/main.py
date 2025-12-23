#!/usr/bin/env python3
# ==============================================================================
# Service: PHYSICS GUARD
# Version: 1.3.0 (Silence Overspeed)
# ==============================================================================

import time
import os
import logging
from influxdb import InfluxDBClient

# --- CONFIGURATION ---
INFLUX_HOST = os.getenv('INFLUX_HOST', 'influxdb')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# Physics Thresholds (Tuned to reduce noise)
MAX_SPEED_KTS = 2000  # Silence alerts for anything under Mach 3
MAX_VSI_FPM   = 8000  # Increased vertical tolerance
MIN_ALT_FT    = -100  

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("PhysicsGuard")

def main():
    logger.info(f"--- PHYSICS GUARD v1.3.0 STARTED ---")
    logger.info(f"    Target: {INFLUX_HOST}:{INFLUX_PORT}")
    
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    while True:
        try:
            client.switch_database(INFLUX_DB)
            logger.info(f"Connected to Database: {INFLUX_DB}")
            break
        except Exception as e:
            logger.warning(f"Waiting for Database... ({e})")
            time.sleep(5)

    while True:
        try:
            query = f"""
                SELECT last("gs_knots") as speed, last("vert_rate") as vsi, 
                       last("alt_baro_ft") as alt, last("callsign") as call
                FROM "local_aircraft_state" 
                WHERE time > now() - 10s 
                GROUP BY "icao24"
            """
            
            results = client.query(query)
            
            for (name, tags), points in results.items():
                p = list(points)[0]
                icao = tags.get('icao24', 'unknown')
                callsign = p.get('call', icao)
                
                speed = float(p.get('speed') or 0)
                vsi   = abs(float(p.get('vsi') or 0))
                alt   = float(p.get('alt') or 0)

                violation = None
                
                if speed > MAX_SPEED_KTS:
                    violation = f"OVERSPEED: {speed} kts"
                elif vsi > MAX_VSI_FPM:
                    violation = f"VERTICAL: {vsi} fpm"
                elif alt < MIN_ALT_FT:
                    violation = f"UNDERGROUND: {alt} ft"

                if violation:
                    logger.warning(f"🚨 PHYSICS ALERT: {callsign} ({icao}) -> {violation}")
                    
                    json_body = [{
                        "measurement": "physics_alerts",
                        "tags": { "icao24": icao, "type": "kinematic" },
                        "fields": {
                            "callsign": str(callsign),
                            "violation": violation,
                            "value": float(speed),
                            "severity": 1.0
                        }
                    }]
                    client.write_points(json_body)

        except Exception as e:
            logger.error(f"Loop Error: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    main()
