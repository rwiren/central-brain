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

# FAKE AIRCRAFT DATA
FAKE_ICAO = "TEST99"
# Fake Position A (Helsinki - Local Sensor)
LAT_A = 60.3172 
LON_A = 24.9633 
# Fake Position B (Tallinn - Truth/OpenSky) - 80km away
LAT_B = 59.4133
LON_B = 24.8328

def main():
    print(f"--- SPOOF SIMULATOR: CONNECTING TO PI AT {pi_ip} ---")
    
    try:
        client = InfluxDBClient(host=pi_ip, port=INFLUX_PORT)
        # Test connection
        client.ping()
        client.switch_database(DB_NAME)
    except Exception as e:
        print(f"ERROR: Could not connect to InfluxDB on the Pi at {pi_ip}:8086")
        print(f"Details: {e}")
        sys.exit(1)

    print(f"--- INJECTING SPOOF DATA FOR {FAKE_ICAO} ---")

    # Loop 5 times to ensure the watchdog catches the overlap in the 60s window
    for i in range(5):
        current_time = datetime.now(timezone.utc).isoformat()
        
        # 1. Inject LOCAL data (Measurement: aircraft)
        # This simulates your Readsb feeder reporting the plane at Helsinki
        json_body_local = [
            {
                "measurement": "aircraft",
                "tags": {
                    "icao": FAKE_ICAO,
                },
                "time": current_time,
                "fields": {
                    "lat": float(LAT_A),
                    "lon": float(LON_A),
                    "alt": 1000.0,
                    "hex": FAKE_ICAO
                }
            }
        ]

        # 2. Inject TRUTH data (Measurement: global_aircraft_state)
        # This simulates OpenSky reporting the SAME plane at Tallinn
        json_body_truth = [
            {
                "measurement": "global_aircraft_state",
                "tags": {
                    "icao24": FAKE_ICAO, 
                },
                "time": current_time,
                "fields": {
                    "lat": float(LAT_B),
                    "lon": float(LON_B),
                    "baro_alt_m": 1000.0
                }
            }
        ]

        # Send to Pi
        client.write_points(json_body_local)
        client.write_points(json_body_truth)
        
        print(f"[{i+1}/5] Data sent to Pi... (Local: HEL, Truth: TLL)")
        time.sleep(5) 

    print("--- INJECTION COMPLETE ---")
    print("Check MQTT Explorer for 'aviation/alerts'")

if __name__ == "__main__":
    main()
