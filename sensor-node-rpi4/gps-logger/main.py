cat > gps-logger/main.py << 'EOF'
"""
GPS Logger Service (GPSD -> InfluxDB)
-------------------------------------
Author:    RW
Version:   1.3.1
Timestamp: 2025-12-02 15:43:00 UTC
Context:   BalenaOS / RPi4 Sensor Node

Description:
    Bridges local GPSD data to a remote InfluxDB instance.
    - Connects to GPSD via TCP socket (port 2947).
    - Streams TPV (Position) and SKY (Satellite/DOP) JSON objects.
    - Normalizes all numeric metrics to FLOAT to prevent InfluxDB type conflicts.
    - Tagging: Forces 'host=rpi4-adsb' to match Grafana dashboard queries.
"""

import socket
import json
import time
import os
import requests
import sys

# --- CONFIGURATION ---
GPSD_HOST = os.getenv('GPSD_HOST', 'gpsd')
GPSD_PORT = int(os.getenv('GPSD_PORT', 2947))
INFLUX_URL = os.getenv('INFLUX_URL', 'http://192.168.1.134:8086')
INFLUX_DB = os.getenv('INFLUX_DB', 'readsb')
TAG_HOST = os.getenv('TAG_HOST', 'rpi4-adsb')

# --- METADATA ---
__version__ = "1.3.1"

def connect_gpsd():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(15)
        s.connect((GPSD_HOST, GPSD_PORT))
        s.sendall(b'?WATCH={"enable":true,"json":true}')
        print(f"[GPS-LOGGER] v{__version__} Connected to {GPSD_HOST}:{GPSD_PORT}")
        return s
    except Exception as e:
        print(f"[ERROR] GPSD Connection Failed: {e}")
        return None

def safe_float(value, default=0.0):
    try:
        if value is None: return default
        return float(value)
    except (TypeError, ValueError):
        return default

def write_to_influx(payload):
    target_url = f"{INFLUX_URL}/write?db={INFLUX_DB}"
    try:
        r = requests.post(target_url, data=payload, timeout=2)
        if r.status_code not in [200, 204]:
            print(f"[INFLUX ERROR] {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[INFLUX EXCEPTION] {e}")

def main():
    print(f"--- GPS Logger Service v{__version__} Started ---")
    sock = None
    buffer = ""
    
    while True:
        if not sock:
            sock = connect_gpsd()
            if not sock:
                time.sleep(5)
                continue

        try:
            data = sock.recv(4096).decode('utf-8')
            if not data:
                print("[WARN] GPSD closed connection. Reconnecting...")
                sock.close(); sock = None; continue
                
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip(): continue

                try:
                    obj = json.loads(line)
                    cls = obj.get("class")
                    payload = None
                    
                    if cls == "TPV":
                        mode = safe_float(obj.get("mode", 1))
                        lat = safe_float(obj.get("lat", 0.0))
                        lon = safe_float(obj.get("lon", 0.0))
                        alt = safe_float(obj.get("alt", 0.0))
                        speed = safe_float(obj.get("speed", 0.0))
                        epx = safe_float(obj.get("epx", 0.0)) 
                        epy = safe_float(obj.get("epy", 0.0)) 
                        epv = safe_float(obj.get("epv", 0.0))

                        payload = (f"gps_data,host={TAG_HOST} "
                                   f"mode={mode},latitude={lat},longitude={lon},"
                                   f"altitude={alt},speed={speed},"
                                   f"epx={epx},epy={epy},epv={epv}")

                    elif cls == "SKY":
                        hdop = safe_float(obj.get("hdop", 99.9))
                        vdop = safe_float(obj.get("vdop", 99.9))
                        pdop = safe_float(obj.get("pdop", 99.9))
                        sats = obj.get("satellites", [])
                        sat_count = float(len(sats))
                        used_count = float(sum(1 for s in sats if s.get('used', False)))

                        payload = (f"gps_data,host={TAG_HOST} "
                                   f"hdop={hdop},vdop={vdop},pdop={pdop},"
                                   f"satellites_visible={sat_count},"
                                   f"satellites_used={used_count}")

                    if payload:
                        write_to_influx(payload)
                            
                except json.JSONDecodeError:
                    pass
                    
        except socket.timeout:
            print("[WARN] GPSD Socket Timeout. Reconnecting...")
            if sock: sock.close(); sock = None
        except Exception as e:
            print(f"[CRITICAL ERROR] {e}")
            if sock: sock.close(); sock = None
            time.sleep(5)

if __name__ == "__main__":
    main()
EOF
