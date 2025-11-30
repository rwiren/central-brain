import time
import sys
from influxdb import InfluxDBClient
from datetime import datetime, timezone

# ==========================================
# CONFIGURATION
# ==========================================
# REPLACE THIS WITH YOUR RASPBERRY PI'S IP ADDRESS
pi_ip = "192.168.1.134" 

INFLUX_PORT = 8086
DB_NAME = 'readsb'

# SCENARIO: Hypersonic Test Vehicle
FAKE_ICAO = "FAST01"
CALLSIGN = "DARKSTAR"

def main():
    print(f"--- PHYSICS BREACH TEST: CONNECTING TO PI AT {pi_ip} ---")
    
    try:
        client = InfluxDBClient(host=pi_ip, port=INFLUX_PORT)
        client.ping()
        client.switch_database(DB_NAME)
    except Exception as e:
        print(f"ERROR: Could not connect to InfluxDB at {pi_ip}: {e}")
        sys.exit(1)

    print(f"--- INJECTING HYPERSONIC DATA FOR {CALLSIGN} ---")

    # We inject 5 points to ensure the 15s polling window catches it
    # We will simulate Mach 3.2 (~2100 knots)
    
    speeds = [400, 900, 1500, 2100, 2150] # Accelerating profile
    
    for i, speed in enumerate(speeds):
        current_time = datetime.now(timezone.utc).isoformat()
        
        mach = speed / 661.47
        
        json_body = [
            {
                "measurement": "aircraft",
                "tags": {
                    "icao": FAKE_ICAO,
                    "callsign": CALLSIGN
                },
                "time": current_time,
                "fields": {
                    "lat": 60.3172, # Over Helsinki
                    "lon": 24.9633,
                    "alt_baro_ft": 60000, # Stratosphere
                    "gs": float(speed),   # Ground Speed (Knots)
                    "vert_rate": 0,
                    "squawk": "7700"
                }
            }
        ]

        client.write_points(json_body)
        
        print(f"[{i+1}/5] Target {CALLSIGN} | Speed: {speed} kts (Mach {mach:.2f})")
        
        if mach > 0.95:
             print(f"      >>> THIS SHOULD TRIGGER A PHYSICS ALERT! <<<")

        time.sleep(5) 

    print("--- TEST COMPLETE ---")
    print("Check MQTT Explorer for 'aviation/alerts' and InfluxDB for 'physics_alerts'")

if __name__ == "__main__":
    main()
