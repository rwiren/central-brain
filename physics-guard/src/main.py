#!/usr/bin/env python3
# ==============================================================================
# Service: PHYSICS GUARD
# Version: 1.4.0 (QNH Compensation)
# Author: Operations Team
# Description: Validates aircraft physics, applying live weather correction.
# ==============================================================================

import time
import os
import logging
from influxdb import InfluxDBClient

# --- CONFIGURATION ---
INFLUX_HOST = os.getenv('INFLUX_HOST', 'influxdb')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# Physics Thresholds
MAX_SPEED_KTS = 2000  # Mach 3+
MAX_VSI_FPM   = 8000  # Vertical Speed
MIN_ALT_FT    = -200  # Alert if lower than this (after QNH correction)

# Airport Elevation (EFHK is ~179 ft)
# We allow some buffer below ground level for calibration errors
AIRPORT_ELEVATION = 179 

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("PhysicsGuard")

def get_qnh(client):
    """
    Fetches the latest QNH (Pressure) from the weather_local measurement.
    Returns standard pressure (1013.25) if unavailable.
    """
    try:
        # Get the most recent pressure reading from the last 15 minutes
        query = 'SELECT last("pressure_hpa") FROM "weather_local" WHERE time > now() - 15m'
        result = client.query(query)
        points = list(result.get_points())
        if points:
            return float(points[0]['last'])
    except Exception:
        pass
    
    return 1013.25 # Fallback to Standard Atmosphere

def main():
    logger.info(f"--- PHYSICS GUARD v1.4.0 (QNH FIXED) STARTED ---")
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
            # 1. Get current Air Pressure
            current_qnh = get_qnh(client)
            
            # Calculate Correction Factor (approx 30ft per hPa)
            # If QNH is 1033 (High), diff is +20. Correction is +600ft.
            alt_correction = (current_qnh - 1013.25) * 30

            # 2. Get Aircraft State
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
                raw_alt = float(p.get('alt') or 0)

                # 3. Apply QNH Correction
                true_alt = raw_alt + alt_correction

                violation = None
                
                if speed > MAX_SPEED_KTS:
                    violation = f"OVERSPEED: {speed} kts"
                elif vsi > MAX_VSI_FPM:
                    violation = f"VERTICAL: {vsi} fpm"
                
                # Check against Ground Level (Elev 179ft) minus buffer
                # If True Alt is significantly below the runway, IT IS underground.
                elif true_alt < (AIRPORT_ELEVATION - 200):
                    violation = f"UNDERGROUND: {int(true_alt)} ft (QNH {int(current_qnh)})"

                if violation:
                    logger.warning(f"🚨 PHYSICS ALERT: {callsign} ({icao}) -> {violation}")
                    
                    json_body = [{
                        "measurement": "physics_alerts",
                        "tags": { "icao24": icao, "type": "kinematic" },
                        "fields": {
                            "callsign": str(callsign),
                            "violation": violation,
                            "value": float(true_alt if "UNDERGROUND" in violation else speed),
                            "qnh_used": float(current_qnh),
                            "severity": 1.0
                        }
                    }]
                    client.write_points(json_body)

        except Exception as e:
            logger.error(f"Loop Error: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    main()
