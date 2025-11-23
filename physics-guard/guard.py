import socket
import time
from influxdb import InfluxDBClient

def main():
    print("Waiting 30s for Database...")
    time.sleep(30) 
    
    # Connect to InfluxDB
    db = InfluxDBClient(host='127.0.0.1', port=8086)
    db.switch_database('readsb')

    # Connect to Local Aggregator (Text Stream on Port 30003)
    # This stream comes from the 'readsb' container on localhost
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 30003))
    f = s.makefile()

    print("Physics Guard Listening for Impossible Flights...")

    for line in f:
        parts = line.split(',')
        if len(parts) > 12 and parts[0] == 'MSG':
            # SBS Format: MSG,1,1,1,440627,1,2025/11/21,12:00:00,2025/11/21,12:00:00,callsign,alt,speed...
            # Index 12 = Ground Speed
            if parts[12].isdigit():
                speed = int(parts[12])
                icao = parts[4]
                
                # RULE: Commercial jets don't fly > 600 knots near airports
                # (Military jets might, but this is a good anomaly check)
                if speed > 600:
                    print(f"🚨 PHYSICS ALARM: {icao} speed {speed} kts!")
                    
                    # Log Alarm to DB
                    json_body = [{
                        "measurement": "physics_alerts",
                        "tags": { "icao": icao, "type": "high_speed" },
                        "fields": { "value": speed }
                    }]
                    db.write_points(json_body)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Physics Guard Error: {e}")
        time.sleep(10)
