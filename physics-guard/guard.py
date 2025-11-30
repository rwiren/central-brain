import time
import os
import requests
import json
import logging
from influxdb import InfluxDBClient
import paho.mqtt.client as mqtt

# --- CONFIGURATION ---

# Database connection
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB = os.getenv('INFLUX_DB', 'readsb')

# MQTT Config
MQTT_BROKER = os.getenv('MQTT_BROKER', '127.0.0.1')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = "aviation/alerts"

# Physics Limits
VSI_LIMIT_FPM = 6000  # Vertical Rate Limit
MACH_LIMIT = 0.95     # Critical Speed Check

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("PhysicsGuard")

# --- MQTT SETUP ---
mqtt_client = mqtt.Client("PhysicsGuard")
mqtt_enabled = False

def setup_mqtt():
    global mqtt_enabled
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        mqtt_enabled = True
        logger.info(f"MQTT Connected to {MQTT_BROKER}")
    except Exception as e:
        logger.warning(f"MQTT Failed ({e}). Alerts will be DB-only.")
        mqtt_enabled = False

def send_alert(client, alert_type, details, icao, value):
    """Logs alert to InfluxDB and publishes to MQTT."""
    
    # 1. Write to InfluxDB (For Grafana History)
    try:
        json_body = [{
            "measurement": "physics_alerts",
            "tags": {"icao": icao, "type": alert_type},
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fields": {"value": float(value), "message": details}
        }]
        client.write_points(json_body)
    except Exception as e:
        logger.error(f"DB Write Error: {e}")

    # 2. Publish to MQTT (For Real-time Notification)
    if mqtt_enabled:
        payload = {
            "type": alert_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": details,
            "icao": icao
        }
        try:
            mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
        except Exception as e:
            logger.error(f"MQTT Publish Error: {e}")

def check_kinematics(client, icao, gs_knots, v_rate_fpm):
    """Implements Mach/VSI checks."""
    
    # 1. VERTICAL RATE CHECK (VSI)
    if v_rate_fpm and abs(v_rate_fpm) > VSI_LIMIT_FPM:
        msg = f"ICAO: {icao} | VSI: {v_rate_fpm} fpm (Limit: {VSI_LIMIT_FPM})"
        logger.warning(f"🚨 {msg}")
        send_alert(client, "PHYSICS_VIOLATION_VSI", msg, icao, v_rate_fpm)
        return True
        
    # 2. MACH/SPEED CHECK
    # Speed of sound approx 661 kts at sea level (simplified)
    if gs_knots:
        speed_of_sound_kts = 661.47 
        mach_number = gs_knots / speed_of_sound_kts
        
        if mach_number > MACH_LIMIT:
            msg = f"ICAO: {icao} | Mach: {mach_number:.2f} (Limit: {MACH_LIMIT})"
            logger.warning(f"🚨 {msg}")
            send_alert(client, "PHYSICS_VIOLATION_MACH", msg, icao, mach_number)
            return True
            
    return False

# --- MAIN LOOP ---

def main():
    logger.info("--- PHYSICS GUARD v0.9 STARTING ---")
    setup_mqtt()
    
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    # Wait for DB
    while True:
        try:
            client.switch_database(INFLUX_DB)
            logger.info(f"Connected to InfluxDB: {INFLUX_DB}")
            break
        except:
            time.sleep(5)
    
    while True:
        try:
            # Query recent aircraft data
            # Adjust 'aircraft' measurement name if your setup is different
            query = f"""
                SELECT last("gs") as speed, last("vert_rate") as vsi
                FROM "aircraft" 
                WHERE time > now() - 15s 
                GROUP BY "icao"
            """
            
            results = client.query(query)
            checked = 0

            for (name, tags), points in results.items():
                checked += 1
                point = list(points)[0]
                icao = tags.get('icao', 'unknown')
                
                # Check Kinematics
                check_kinematics(client, icao, point.get('speed'), point.get('vsi'))

            if checked > 0:
                logger.debug(f"Physics checked on {checked} targets.")

        except Exception as e:
            logger.error(f"Loop Error: {e}")
        
        time.sleep(15)

if __name__ == "__main__":
    main()
