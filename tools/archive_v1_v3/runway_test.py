import time
from influxdb import InfluxDBClient

# --- CONFIGURATION ---
INFLUX_HOST = '192.168.1.134' 
INFLUX_PORT = 8086
DB_NAME = 'readsb'

def main():
    print(f"--- RUNWAY EVENT TESTER: Connecting to {INFLUX_HOST} ---")
    
    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    client.switch_database(DB_NAME)

    print("Injecting: FIN999 | Landing | Runway 15")
    
    json_body = [
        {
            "measurement": "runway_events",
            "tags": {
                "event": "landing",
                "runway": "15"
            },
            "fields": {
                "callsign": "FIN999",
                "altitude": 450.0,  # Float
                "speed": 138.0,     # Float
                "squawk": "4621",   # String
                "value": 1.0        # FIX: Changed 1 to 1.0 (Float)
            }
        }
    ]
    
    try:
        client.write_points(json_body)
        print("✅ Data successfully sent!")
        print("Check your Grafana 'Live Runway' panel immediately.")
    except Exception as e:
        print(f"❌ Error writing to DB: {e}")

if __name__ == "__main__":
    main()
