import time
import os
import sys
import psutil # Now available via requirements.txt
from influxdb import InfluxDBClient

# --- CONFIGURATION ---
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

# Device Name
DEVICE_NAME = os.getenv('DEVICE_NAME', os.getenv('BALENA_DEVICE_NAME_AT_INIT', os.uname()[1]))

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
    """Captures RAM and Disk usage."""
    # Memory
    ram = psutil.virtual_memory()
    # Disk (Root partition)
    disk = psutil.disk_usage('/')
    
    return ram.percent, disk.percent

def main():
    print(f"System Observer [{DEVICE_NAME}] Starting...", flush=True)
    print(f"Target: {INFLUX_HOST}:{INFLUX_PORT} (DB: {INFLUX_DB})", flush=True)
    
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    # --- Database Initialization ---
    while True:
        try:
            # Only create DB if running locally/admin
            if INFLUX_HOST in ['127.0.0.1', 'localhost', 'influxdb']:
                dbs = client.get_list_database()
                if not any(d['name'] == INFLUX_DB for d in dbs):
                    client.create_database(INFLUX_DB)
            
            client.switch_database(INFLUX_DB)
            print("Connected to InfluxDB", flush=True)
            break
        except Exception as e:
            print(f"Database Connection Failed ({e}). Retrying in 5s...", flush=True)
            time.sleep(5)

    # --- Main Loop ---
    while True:
        try:
            temp = get_cpu_temp()
            uptime = get_uptime()
            ram_usage, disk_usage = get_system_metrics()
            
            json_body = [
                {
                    "measurement": "system_stats",
                    "tags": {
                        "host": DEVICE_NAME
                    },
                    "fields": {
                        "cpu_temp": float(temp),
                        "uptime": int(uptime),
                        "ram_usage": float(ram_usage),
                        "disk_usage": float(disk_usage)
                    }
                }
            ]
            
            client.write_points(json_body)
            # FIX: Removed '°' symbol to prevent log artifacts
            print(f"[{DEVICE_NAME}] Stats Pushed: {temp} C | RAM: {ram_usage}%", flush=True)
            
        except Exception as e:
            print(f"Write Error: {e}", flush=True)
            
        time.sleep(10)

if __name__ == "__main__":
    main()
