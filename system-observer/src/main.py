import time
import os
import sys
import psutil 
from influxdb import InfluxDBClient
import logging

# --- CONFIGURATION ---
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# Device Name
DEVICE_NAME = os.getenv('DEVICE_NAME', os.getenv('BALENA_DEVICE_NAME_AT_INIT', os.uname()[1]))

# Logging setup (Optional, but good practice for tracking status)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("SystemObserver")


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
    # Memory
    ram = psutil.virtual_memory()
    # CPU usage (non-blocking for quick check)
    cpu_usage = psutil.cpu_percent(interval=None) 
    # Disk (Root partition)
    disk = psutil.disk_usage('/')
    
    # Return CPU, RAM, Disk, Temp
    return cpu_usage, ram.percent, disk.percent 

def main():
    logger.info(f"System Observer [{DEVICE_NAME}] Starting...")
    logger.info(f"Target: {INFLUX_HOST}:{INFLUX_PORT} (DB: {INFLUX_DB})")
    
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    # --- Database Initialization / Connection Check ---
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

    # --- Main Loop ---
    while True:
        try:
            temp = get_cpu_temp()
            uptime = get_uptime()
            cpu_usage, ram_usage, disk_usage = get_system_metrics()
            
            json_body = [
                {
                    "measurement": "system_stats",
                    "tags": {
                        "host": DEVICE_NAME,
                        "cpu_model": os.uname().machine # Optional: Add architecture tag
                    },
                    "fields": {
                        "cpu_temp": float(temp),
                        "uptime": int(uptime),
                        "cpu_usage": float(cpu_usage),
                        "ram_usage": float(ram_usage),
                        "disk_usage": float(disk_usage) # <-- CRITICAL FIX: DISK USAGE ADDED
                    }
                }
            ]
            
            client.write_points(json_body)
            # Log disk usage percentage for debugging
            logger.info(f"Stats Pushed: {temp} C | RAM: {ram_usage}% | DISK: {disk_usage}%")
            
        except Exception as e:
            logger.error(f"Write Error: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    main()
