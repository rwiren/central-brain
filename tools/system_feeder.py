import time
import os
from influxdb import InfluxDBClient

# --- CONFIGURATION ---
INFLUX_HOST = 'localhost'
INFLUX_PORT = 8086
INFLUX_DB   = 'central_brain' # Make sure this matches your DB name

def get_cpu_temp():
    """Reads the Raspberry Pi CPU temperature."""
    try:
        # Method 1: The standard Linux thermal zone (works on Pi and most Linux PCs)
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read()
        return int(temp_str) / 1000.0
    except:
        return 0.0

def get_uptime():
    """Gets system uptime in seconds."""
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        return int(uptime_seconds)
    except:
        return 0

def main():
    print("❤️  Starting System Health Feeder...")
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    
    # Ensure database exists
    client.create_database(INFLUX_DB)
    client.switch_database(INFLUX_DB)

    while True:
        temp = get_cpu_temp()
        uptime = get_uptime()
        
        json_body = [
            {
                "measurement": "system_stats",
                "tags": {
                    "host": "node_1_anchor"
                },
                "fields": {
                    "cpu_temp": float(temp),
                    "uptime": int(uptime)
                }
            }
        ]
        
        try:
            client.write_points(json_body)
            print(f"✅ Pushed Health Data: Temp={temp}°C, Uptime={uptime}s")
        except Exception as e:
            print(f"❌ Write Failed: {e}")
            
        time.sleep(5) # Update every 5 seconds

if __name__ == "__main__":
    main()
