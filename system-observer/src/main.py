import time
import os
import sys
import psutil 
from influxdb import InfluxDBClient
import logging
import requests
import json

# --- CONFIGURATION ---
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# Device Name
DEVICE_NAME = os.getenv('DEVICE_NAME', os.getenv('BALENA_DEVICE_NAME_AT_INIT', os.uname()[1]))

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("SystemObserver")

# --- SYSTEM METRICS FUNCTIONS ---
def get_cpu_temp():
    """Reads temperature from thermal zone (Raspberry Pi specific)."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read()
        return round(float(temp_str) / 1000.0, 2)
    except:
        return 0.0

def get_uptime():
    """Reads system uptime."""
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        return int(uptime_seconds)
    except:
        return 0

def get_system_metrics():
    """Collects CPU, RAM, and Disk usage using psutil."""
    ram = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent(interval=None) 
    disk = psutil.disk_usage('/')
    return cpu_usage, ram.percent, disk.percent 

# --- WEATHER FUNCTION ---
def fetch_metar_data():
    """
    Fetches live aviation weather for EFHK (Vantaa) from NOAA.
    Returns InfluxDB JSON body or None.
    """
    # NOAA Aviation Weather Center API (Global Data, Clean JSON)
    url = "https://aviationweather.gov/api/data/metar?ids=EFHK&format=json"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and len(response.json()) > 0:
            data = response.json()[0]
            
            # Parse visibility (handle '10+' string)
            vis_str = str(data.get('visib', '10')).replace('+', '')
            try:
                visibility_miles = float(vis_str)
            except:
                visibility_miles = 10.0

            json_body = [
                {
                    "measurement": "weather_local",
                    "tags": {
                        "station": "EFHK"
                    },
                    "fields": {
                        "temperature_c": float(data.get('temp', 0)),
                        "dewpoint_c": float(data.get('dewp', 0)),
                        "wind_speed_kt": float(data.get('wspd', 0)),
                        "wind_dir_deg": float(data.get('wdir', 0)),
                        "pressure_hpa": float(data.get('altim', 1013)),
                        "visibility_miles": visibility_miles,
                        "raw_metar": data.get('rawOb', "N/A") 
                    }
                }
            ]
            return json_body
    except Exception as e:
        logger.error(f"METAR Fetch Error: {e}")
        return None

# --- MAIN LOOP ---
def main():
    logger.info(f"System Observer [{DEVICE_NAME}] Starting...")
    logger.info(f"Target: {INFLUX_HOST}:{INFLUX_PORT} (DB: {INFLUX_DB})")
    
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    # --- Database Initialization ---
    while True:
        try:
            # Create database if necessary (only runs on central host)
            if INFLUX_HOST in ['127.0.0.1', 'localhost', 'influxdb']:
                dbs = client.get_list_database()
                if not any(d['name'] == INFLUX_DB for d in dbs):
                    client.create_database(INFLUX_DB)
            
            client.switch_database(INFLUX_DB)
            logger.info("Connected to InfluxDB")
            break
        except Exception as e:
            logger.error(f"Database Connection Failed ({e}). Retrying in 5s...")
            time.sleep(5)

    # Timers
    last_weather_check = 0
    weather_interval = 300  # Check weather every 5 minutes

    while True:
        try:
            # 1. Collect System Stats (Every Loop - 10s)
            temp = get_cpu_temp()
            uptime = get_uptime()
            cpu_usage, ram_usage, disk_usage = get_system_metrics()
            
            system_body = [
                {
                    "measurement": "system_stats",
                    "tags": {
                        "host": DEVICE_NAME,
                        "cpu_model": os.uname().machine
                    },
                    "fields": {
                        "cpu_temp": float(temp),
                        "uptime": int(uptime),
                        "cpu_usage": float(cpu_usage),
                        "ram_usage": float(ram_usage),
                        "disk_usage": float(disk_usage)
                    }
                }
            ]
            client.write_points(system_body)
            logger.info(f"Stats Pushed: {temp} C | RAM: {ram_usage}% | DISK: {disk_usage}%")

            # 2. Collect Weather (Every 5 mins)
            if time.time() - last_weather_check > weather_interval:
                weather_data = fetch_metar_data()
                if weather_data:
                    client.write_points(weather_data)
                    logger.info(f"Weather Updated: {weather_data[0]['fields']['raw_metar']}")
                last_weather_check = time.time()
            
        except Exception as e:
            logger.error(f"Main Loop Error: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    main()
