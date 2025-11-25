import time
import os
import json
import logging
from influxdb import InfluxDBClient
from geopy.distance import geodesic
import paho.mqtt.client as mqtt

# ==========================================
# CONFIGURATION
# ==========================================

# 1. InfluxDB Settings (The Central Brain)
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1') # or central-brain if running remote
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# 2. Measurements to Compare
# 'global_aircraft_state' is what we set up in adsb-feeders to hold OpenSky data
MEASUREMENT_TRUTH = "global_aircraft_state" 
# 'aircraft' or 'readsb' is usually the default for local data. 
# Adjust if your local feeder uses a different name.
MEASUREMENT_LOCAL = os.getenv('MEASUREMENT_LOCAL', 'aircraft') 

# 3. Thresholds
DIST_THRESHOLD_KM = 2.0  # Trigger alert if difference is > 2km

# 4. MQTT Config (For Alerts)
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC_ALERTS = "aviation/alerts"

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("spoof-watchdog")

# ==========================================
# MQTT SETUP
# ==========================================
mqtt_client = mqtt.Client("SpoofDetector")
mqtt_enabled = False

def setup_mqtt():
    global mqtt_enabled
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        mqtt_enabled = True
        logger.info(f"MQTT Connected to {MQTT_BROKER}")
    except Exception as e:
        logger.warning(f"MQTT Failed ({e}). Running in Console-Only mode.")
        mqtt_enabled = False

def send_alert(alert_type, details):
    """Sends alert via MQTT and Logs."""
    msg = {
        "type": alert_type,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details
    }
    
    # Console
    logger.critical(f"🚨 {alert_type}: {details}")
    
    # MQTT
    if mqtt_enabled:
        try:
            mqtt_client.publish(MQTT_TOPIC_ALERTS, json.dumps(msg))
        except:
            pass

# ==========================================
# DATABASE FUNCTIONS
# ==========================================
def get_latest_positions(client, measurement):
    """
    Fetches the most recent position for every aircraft seen in the last 60s.
    Returns: Dict { 'icao_hex': {'lat': float, 'lon': float, 'alt': float} }
    """
    data = {}
    try:
        # Query: Get the last recorded point for every aircraft in the last minute
        # We group by 'icao24' (OpenSky) or 'icao' (Local) or 'hex' depending on schema
        # This generic query attempts to find tags automatically.
        query = f"""
            SELECT last("lat") as lat, last("lon") as lon, last("alt") as alt, last("baro_alt_m") as alt_m
            FROM "{measurement}" 
            WHERE time > now() - 60s 
            GROUP BY *
        """
        
        results = client.query(query)
        
        for (name, tags), points in results.items():
            # Try to find the ICAO hex code in the tags
            icao = tags.get('icao24') or tags.get('icao') or tags.get('hex') or tags.get('addr')
            
            if icao:
                point = list(points)[0]
                # Normalize Altitude (OpenSky uses 'baro_alt_m', some locals use 'alt')
                alt = point.get('alt_m') if point.get('alt_m') is not None else point.get('alt')
                
                if point['lat'] is not None and point['lon'] is not None:
                    data[icao.lower()] = {
                        'lat': float(point['lat']),
                        'lon': float(point['lon']),
                        'alt': float(alt) if alt else 0.0
                    }
    except Exception as e:
        logger.error(f"Query Error ({measurement}): {e}")
        
    return data

# ==========================================
# MAIN LOOP
# ==========================================
def main():
    logger.info("--- SPOOF DETECTOR (InfluxDB Backend) STARTING ---")
    setup_mqtt()
    
    db_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    # Wait for DB connection
    while True:
        try:
            db_client.switch_database(INFLUX_DB)
            logger.info(f"Connected to InfluxDB: {INFLUX_DB}")
            break
        except Exception as e:
            logger.warning(f"Waiting for InfluxDB... ({e})")
            time.sleep(5)

    # Analysis Loop
    while True:
        try:
            # 1. Get Truth (OpenSky)
            truth_data = get_latest_positions(db_client, MEASUREMENT_TRUTH)
            
            # 2. Get Local (Readsb)
            local_data = get_latest_positions(db_client, MEASUREMENT_LOCAL)
            
            if not truth_data:
                logger.info("Waiting for OpenSky data (Truth source is empty)...")
            
            # 3. Compare
            matches = 0
            anomalies = 0
            
            for icao, local_pos in local_data.items():
                if icao in truth_data:
                    matches += 1
                    truth_pos = truth_data[icao]
                    
                    # Calculate physical distance between reported positions
                    p1 = (local_pos['lat'], local_pos['lon'])
                    p2 = (truth_pos['lat'], truth_pos['lon'])
                    
                    distance = geodesic(p1, p2).km
                    
                    if distance > DIST_THRESHOLD_KM:
                        anomalies += 1
                        details = (
                            f"ICAO: {icao} | "
                            f"Local: {p1} | "
                            f"OpenSky: {p2} | "
                            f"Diff: {distance:.2f}km"
                        )
                        send_alert("GPS SPOOFING DETECTED", details)
            
            if matches > 0:
                logger.info(f"Scanned {len(local_data)} local aircraft. Matches: {matches}. Spoofing Alerts: {anomalies}")
            else:
                logger.debug(f"Scanning... Local: {len(local_data)} | Truth: {len(truth_data)}")

        except Exception as e:
            logger.error(f"Loop Error: {e}")

        # Sleep interval (OpenSky updates every 10-20s, so checking every 15s is efficient)
        time.sleep(15)

if __name__ == "__main__":
    main()
