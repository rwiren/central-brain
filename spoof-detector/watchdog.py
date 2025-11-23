import os
import time
import socket
import threading
import math
from datetime import datetime
from collections import deque
from opensky_api import OpenSkyApi
from influxdb import InfluxDBClient

# ==========================================
# CONFIGURATION
# ==========================================

# 1. Env Variables
OPENSKY_USER = os.getenv('OPENSKY_USERNAME')
OPENSKY_PASS = os.getenv('OPENSKY_PASSWORD')
INFLUX_HOST = os.getenv('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = int(os.getenv('INFLUX_PORT', 8086))
INFLUX_USER = os.getenv('INFLUX_USER', 'admin')
INFLUX_PASS = os.getenv('INFLUX_PASSWORD', 'admin')
INFLUX_DB   = os.getenv('INFLUX_DB', 'readsb')

READSB_HOST = os.getenv('READSB_HOST', '127.0.0.1')
READSB_PORT = int(os.getenv('READSB_PORT', 30003))

# 2. Geometry & Logic
MY_LAT, MY_LON = 60.3172, 24.9633 # Approx Vantaa Center
EFHK_LAT, EFHK_LON = 60.3172, 24.9633 # Helsinki Airport

# Helsinki Runway Headings (Approximate)
RUNWAYS = {
    "22L": (220, 230), "04R": (40, 50),
    "22R": (220, 230), "04L": (40, 50),
    "15":  (140, 160), "33":  (320, 340)
}

# 3. Global State
global_aircraft = {}
local_tracker = {}
lock = threading.Lock()

# History tracker for behavior analysis (Last 5 points per plane)
flight_history = {} 

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_influx_client():
    try:
        client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, username=INFLUX_USER, password=INFLUX_PASS)
        client.switch_database(INFLUX_DB)
        return client
    except Exception as e:
        print(f"[Error] InfluxDB: {e}")
        return None

def get_distance_bearing(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius km
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r
    a = math.sin(dlat / 2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    x = math.sin(dlon) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - (math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon))
    bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
    return distance, bearing

def identify_runway(lat, lon, heading, alt):
    # Must be low altitude (< 3000ft) and close to airport (< 10km)
    dist, _ = get_distance_bearing(EFHK_LAT, EFHK_LON, lat, lon)
    if dist < 10 and alt < 3000:
        for rwy, (min_h, max_h) in RUNWAYS.items():
            if min_h <= heading <= max_h:
                return rwy
    return "Unknown"

# ==========================================
# THREAD 1: OPENSKY (TRUTH)
# ==========================================
def fetch_opensky():
    # ... (Keeping your existing OpenSky logic here - simplified for brevity)
    # Make sure to include the "Updated Box" from previous steps
    BBOX = (58.50, 61.50, 22.00, 27.00) 
    try:
        api = OpenSkyApi(OPENSKY_USER, OPENSKY_PASS)
    except:
        return

    db = get_influx_client()
    while True:
        try:
            states = api.get_states(bbox=BBOX)
            count = len(states.states) if states else 0
            if states:
                with lock:
                    global global_aircraft
                    global_aircraft = {s.icao24: {'lat': s.latitude, 'lon': s.longitude} for s in states.states}
            
            if db:
                db.write_points([{
                    "measurement": "global_truth",
                    "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "fields": { "aircraft_count": int(count) }
                }])
        except:
            pass
        time.sleep(30)

# ==========================================
# THREAD 2: BEHAVIOR ANALYZER (LOCAL)
# ==========================================
def listen_local():
    time.sleep(5)
    db = get_influx_client()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            s.connect((READSB_HOST, READSB_PORT))
            f = s.makefile()
            print("[Local] Connected to Receiver!")
            break
        except:
            time.sleep(5)

    for line in f:
        try:
            parts = line.split(',')
            # MSG, transmissionType, sessionID, aircraftID, HexIdent, FlightID, Date, Time, Date, Time, Call, Alt, GSpeed, Track, Lat, Long, VRate, Squawk, Alert, Emergency, SPI, IsOnGround
            if len(parts) > 16 and parts[0] == 'MSG':
                
                # DATA PARSING
                icao = parts[4]
                callsign = parts[10].strip()
                
                # Safe casting
                try:
                    lat = float(parts[14])
                    lon = float(parts[15])
                    alt = float(parts[11]) if parts[11] else 0.0
                    speed = float(parts[12]) if parts[12] else 0.0
                    track = float(parts[13]) if parts[13] else 0.0
                    v_rate = float(parts[16]) if parts[16] else 0.0 # Vertical Rate
                    on_ground = int(parts[21]) if len(parts) > 21 and parts[21] else 0
                except ValueError:
                    continue

                # 1. CALCULATE GEOMETRICS
                dist_km, bearing_deg = get_distance_bearing(MY_LAT, MY_LON, lat, lon)
                runway = identify_runway(lat, lon, track, alt)
                
                # 2. DETECT ANOMALIES (Go-Around / Steep Turn)
                event_tag = "Normal"
                
                # Get history
                if icao not in flight_history:
                    flight_history[icao] = deque(maxlen=5)
                
                history = flight_history[icao]
                history.append({'alt': alt, 'v_rate': v_rate, 'speed': speed, 'time': time.time()})

                # ANALYSIS LOGIC
                if len(history) >= 2:
                    prev = history[-2]
                    curr = history[-1]
                    
                    # A. GO-AROUND DETECTION
                    # If low altitude (< 2000ft), was descending, now climbing fast
                    if alt < 2000 and prev['v_rate'] < -200 and curr['v_rate'] > 500:
                        event_tag = "Go-Around"
                        print(f"🚨 GO-AROUND DETECTED: {icao} {callsign}")

                    # B. STEEP ASCENT/DESCENT (Commercial Jets usually max 3000fpm)
                    elif curr['v_rate'] > 4000:
                        event_tag = "Steep Climb"
                    elif curr['v_rate'] < -4000:
                        event_tag = "Rapid Descent"

                    # C. CANCELLED TAKEOFF (Experimental)
                    # On ground, speed > 40 knots, then suddenly 0 knots
                    elif on_ground == 1 and prev['speed'] > 40 and curr['speed'] < 5:
                        event_tag = "Rejected Takeoff"

                # 3. SPOOF CHECK
                spoof_flag = 0
                with lock:
                    if icao in global_aircraft:
                        g_lat = global_aircraft[icao]['lat']
                        g_lon = global_aircraft[icao]['lon']
                        if g_lat and abs(lat - g_lat) > 0.02:
                            spoof_flag = 1

                # 4. WRITE ENHANCED DATA
                dt_object = datetime.now()
                
                if db:
                    json_body = [{
                        "measurement": "flight_ops",
                        "tags": { 
                            "icao": icao,
                            "runway_guess": runway,
                            "event_type": event_tag,
                            "weekday": dt_object.strftime('%A'),
                            "hour": dt_object.strftime('%H'),
                            "source": "local_enhanced"
                        },
                        "fields": {
                            "lat": lat,
                            "lon": lon,
                            "alt_ft": int(alt),
                            "speed_kts": int(speed),
                            "vertical_rate": int(v_rate),
                            "distance_km": float(dist_km),
                            "bearing_deg": float(bearing_deg),
                            "is_spoofed": int(spoof_flag),
                            "event_score": 1 if event_tag != "Normal" else 0
                        }
                    }]
                    db.write_points(json_body)

        except Exception as e:
            continue

if __name__ == "__main__":
    t1 = threading.Thread(target=fetch_opensky)
    t1.daemon = True
    t1.start()
    listen_local()
