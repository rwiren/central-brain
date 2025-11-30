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
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

MEASUREMENT_TRUTH = "global_aircraft_state" 
MEASUREMENT_LOCAL = os.getenv('MEASUREMENT_LOCAL', 'aircraft') 

DIST_THRESHOLD_KM = 2.0 

MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC_ALERTS = "aviation/alerts"

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

def report_to_influx(client, measurement, tags, fields):
    try:
        json_body = [{
            "measurement": measurement,
            "tags": tags,
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fields": fields
        }]
        client.write_points(json_body)
    except Exception as e:
        logger.error(f"Failed to write to Influx: {e}")

# UPDATED: Now accepts positions to save them to the DB
def send_alert(client, alert_type, details, icao, diff_km, local_pos, truth_pos):
    """Sends alert via MQTT and writes detailed data to InfluxDB."""
    msg = {
        "type": alert_type,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details
    }
    
    # 1. Console
    logger.critical(f"🚨 {alert_type}: {details}")
    
    # 2. MQTT
    if mqtt_enabled:
        try:
            mqtt_client.publish(MQTT_TOPIC_ALERTS, json.dumps(msg))
        except:
            pass

    # 3. InfluxDB (Rich Data for Table)
    # We save floats so Grafana can format them nicely
    report_to_influx(client, "security_alerts", 
                     {"type": "spoofing", "icao": icao}, 
                     {
                         "message": details, 
                         "diff_km": float(diff_km), 
                         "alert_val": 1,
                         "fr24_lat": float(truth_pos['lat']),
                         "fr24_lon": float(truth_pos['lon']),
                         "local_lat": float(local_pos['lat']),
                         "local_lon": float(local_pos['lon'])
                     })

# ==========================================
# DATABASE FUNCTIONS
# ==========================================
def get_latest_positions(client, measurement):
    data = {}
    try:
        query = f"""
            SELECT last("lat") as lat, last("lon") as lon, last("alt") as alt, last("baro_alt_m") as alt_m
            FROM "{measurement}" 
            WHERE time > now() - 60s 
            GROUP BY *
        """
        results = client.query(query)
        for (name, tags), points in results.items():
            icao = tags.get('icao24') or tags.get('icao') or tags.get('hex') or tags.get('addr')
            if icao:
                point = list(points)[0]
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
    logger.info("--- SPOOF DETECTOR v2.1 (Expanded Logging) STARTING ---")
    setup_mqtt()
    
    db_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    while True:
        try:
            db_client.switch_database(INFLUX_DB)
            logger.info(f"Connected to InfluxDB: {INFLUX_DB}")
            break
        except Exception as e:
            logger.warning(f"Waiting for InfluxDB... ({e})")
            time.sleep(5)

    while True:
        try:
            truth_data = get_latest_positions(db_client, MEASUREMENT_TRUTH)
            local_data = get_latest_positions(db_client, MEASUREMENT_LOCAL)
            
            if not truth_data:
                logger.info("Waiting for OpenSky/FR24 data...")
            
            matches = 0
            
            for icao, local_pos in local_data.items():
                if icao in truth_data:
                    matches += 1
                    truth_pos = truth_data[icao]
                    
                    p1 = (local_pos['lat'], local_pos['lon'])
                    p2 = (truth_pos['lat'], truth_pos['lon'])
                    distance = geodesic(p1, p2).km
                    
                    # Drift Metric
                    report_to_influx(db_client, "gps_drift", 
                                     {"icao": icao}, 
                                     {"drift_km": float(distance)})
                    
                    if distance > DIST_THRESHOLD_KM:
                        details = f"ICAO: {icao} | Diff: {distance:.2f}km"
                        # UPDATED CALL: Passing positions
                        send_alert(db_client, "GPS SPOOFING DETECTED", details, icao, distance, local_pos, truth_pos)
            
            if matches > 0:
                logger.info(f"Scanned {len(local_data)} aircraft. Matches: {matches}.")
                
        except Exception as e:
            logger.error(f"Loop Error: {e}")

        time.sleep(15)

if __name__ == "__main__":
    main()
