import requests
import time
import sys

# ==============================================================================
# Script: live_labeler.py
# Purpose: Auto-labels data for AI (e.g., "TAKEOFF", "LANDING", "HOLDING")
# Logic: Analyzes Physics (Vertical Rate + Altitude + Turn Rate)
# ==============================================================================

INFLUX_HOST = "http://192.168.1.134:8086"
DB_NAME = "readsb"

# Thresholds
LANDING_ALT = 2500      # ft (Below this, we watch for landing)
CLIMB_RATE = 500        # fpm
DESCENT_RATE = -500     # fpm
TURN_THRESHOLD = 3.0    # degrees per second (Standard Rate Turn)

def get_active_flights():
    """Fetches the last minute of physics data."""
    q = 'SELECT last("alt_baro_ft"), last("vert_rate_fpm"), last("track"), last("gs_knots") FROM "local_aircraft_state" WHERE time > now() - 1m GROUP BY "icao24", "callsign"'
    try:
        r = requests.get(f"{INFLUX_HOST}/query", params={'db': DB_NAME, 'q': q})
        return r.json()
    except:
        return None

def classify_maneuver(alt, vs, speed):
    """The 'Teacher' Logic - Rules to label the data."""
    if speed < 50 and alt < 100:
        return "TAXI / PARKED"
    
    if alt < LANDING_ALT:
        if vs < DESCENT_RATE:
            return "FINAL APPROACH"
        elif vs > CLIMB_RATE:
            return "TAKEOFF / GO-AROUND"
    
    if alt > 30000 and -100 < vs < 100:
        return "CRUISE"
        
    return "EN_ROUTE" # Default

def main():
    print("--- 🏷️  LIVE AI DATA LABELER ---")
    print("Watching for flight maneuvers...")
    
    while True:
        data = get_active_flights()
        
        if data and 'results' in data and 'series' in data['results'][0]:
            print("\n--- Current Airspace Activity ---")
            for series in data['results'][0]['series']:
                tags = series.get('tags', {})
                vals = series['values'][0]
                
                # Extract Physics
                callsign = tags.get('callsign', 'N/A')
                icao = tags.get('icao24', 'N/A')
                alt = vals[1] if vals[1] is not None else 0
                vs = vals[2] if vals[2] is not None else 0
                speed = vals[4] if vals[4] is not None else 0
                
                # Apply Logic
                label = classify_maneuver(alt, vs, speed)
                
                # Visual Output
                icon = "✈️"
                if "LANDING" in label: icon = "🛬"
                elif "TAKEOFF" in label: icon = "🛫"
                elif "CRUISE" in label: icon = "⏩"
                
                print(f"{icon} {callsign:<8} | Alt: {alt:>5}ft | VS: {vs:>5}fpm | {label}")
                
        time.sleep(5)

if __name__ == "__main__":
    main()
