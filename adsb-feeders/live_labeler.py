import requests
import time
import os
import sys

# ==============================================================================
# Service: live_labeler.py
# Role: AI Training Supervisor
# Description: Monitors physics and writes 'Ground Truth' labels to InfluxDB.
# ==============================================================================

INFLUX_HOST = os.getenv("INFLUX_HOST", "http://influxdb:8086")
DB_NAME = "readsb"
WRITE_URL = f"{INFLUX_HOST}/write?db={DB_NAME}"

# Physics Thresholds
LANDING_ALT = 1500      
TAKEOFF_VS = 500        
LANDING_VS = -300       
CRUISE_ALT = 25000      

def get_snapshot():
    q = 'SELECT last("alt_baro_ft"), last("vert_rate_fpm"), last("gs_knots"), last("track") FROM "local_aircraft_state" WHERE time > now() - 1m GROUP BY "icao24", "callsign"'
    try:
        r = requests.get(f"{INFLUX_HOST}/query", params={'db': DB_NAME, 'q': q}, timeout=5)
        return r.json()
    except Exception as e:
        print(f"Query Error: {e}")
        return None

def classify(alt, vs, speed):
    if alt < 200 and speed < 40: return "TAXI_PARKED"
    if alt < LANDING_ALT:
        if vs < LANDING_VS: return "FINAL_APPROACH"
        elif vs > TAKEOFF_VS: return "TAKEOFF_CLIMB"
        elif speed > 120: return "LOW_PASS"
    if alt > CRUISE_ALT and -100 < vs < 100: return "CRUISE_FLIGHT"
    if vs > 1500: return "RAPID_CLIMB"
    if vs < -1500: return "RAPID_DESCENT"
    return "EN_ROUTE"

def main():
    print("--- 🤖 AI LABELING SERVICE STARTED ---")
    
    while True:
        data = get_snapshot()
        if data and 'results' in data and 'series' in data['results'][0]:
            lines = []
            now_ns = int(time.time() * 1e9)
            
            for series in data['results'][0]['series']:
                tags = series.get('tags', {})
                icao = tags.get('icao24', 'unknown')
                callsign = tags.get('callsign', 'unknown')
                
                vals = series['values'][0]
                alt = vals[1] if vals[1] is not None else 0
                vs = vals[2] if vals[2] is not None else 0
                speed = vals[3] if vals[3] is not None else 0
                
                label = classify(alt, vs, speed)
                
                # Write to 'ai_training_labels' table
                line = f"ai_training_labels,icao24={icao},callsign={callsign},maneuver={label} alt_ft={int(alt)}i,vs_fpm={int(vs)}i,confidence=1.0 {now_ns}"
                lines.append(line)
            
            if lines:
                try:
                    requests.post(WRITE_URL, data="\n".join(lines), timeout=5)
                    # Log interesting events for verification
                    for l in lines:
                        if "TAKEOFF" in l or "FINAL" in l:
                            print(f"🏷️  LABELED: {l.split(',')[2]} -> {l.split(',')[3].split(' ')[0]}")
                except:
                    pass

        time.sleep(5)

if __name__ == "__main__":
    main()
