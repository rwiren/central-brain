import time
import os
import psutil
from influxdb import InfluxDBClient
import logging

# --- CONFIGURATION ---
# RPi4 sends data TO the Central Brain IP
INFLUX_HOST = os.getenv('INFLUX_HOST', '192.168.1.134') # Update to your RPi5 IP
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# Automatic Device Name (e.g., "RPi4-Sensor")
DEVICE_NAME = os.getenv('BALENA_DEVICE_NAME_AT_INIT', os.uname()[1])

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("SystemObserver-Sensor")

def get_metrics():
    """Collects hardware stats."""
    # CPU Temp
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = round(float(f.read()) / 1000.0, 2)
    except: temp = 0.0

    # Uptime
    try:
        with open("/proc/uptime", "r") as f:
            uptime = int(float(f.readline().split()[0]))
    except: uptime = 0

    # Usage
    ram = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent(interval=None)
    disk = psutil.disk_usage('/').percent
    
    return temp, uptime, cpu, ram, disk

def main():
    logger.info(f"--- Sensor Node Observer Started ({DEVICE_NAME}) ---")
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)

    while True:
        try:
            temp, uptime, cpu, ram, disk = get_metrics()

            json_body = [
                {
                    "measurement": "system_stats",
                    "tags": {
                        "host": "RPi4-Sensor", # Hardcoded tag for Dashboard filtering
                        "role": "sensor_node"
                    },
                    "fields": {
                        "cpu_temp": float(temp),
                        "uptime": int(uptime),
                        "cpu_usage": float(cpu),
                        "ram_usage": float(ram),
                        "disk_usage": float(disk) # Added to match Central Brain schema
                    }
                }
            ]
            client.write_points(json_body, database=INFLUX_DB)
            logger.info(f"Pushed: {temp}°C | CPU: {cpu}% | DISK: {disk}%")

        except Exception as e:
            logger.error(f"Connection Error to Central Brain: {e}")
        
        time.sleep(10)

if __name__ == "__main__":
    main()
