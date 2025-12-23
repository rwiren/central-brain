import time
import sys
import requests
from datetime import datetime, timezone

# ==========================================
# Script: spoof_simulator_v2.py
# Description: Injects Level 4 Spoofing Data
# Target: local_aircraft_state (The AI Table)
# Fix: v2.1 (Type Conflict Resolution)
# ==========================================

PI_IP = "192.168.1.134" 
INFLUX_PORT = 8086
DB_NAME = 'readsb'
WRITE_URL = f"http://{PI_IP}:{INFLUX_PORT}/write?db={DB_NAME}"

# SCENARIO: "The Phantom Plane"
FAKE_ICAO = "SPOOF99"
LAT_LOCAL = 60.3172  # Helsinki
LON_LOCAL = 24.9633
LAT_TRUTH = 59.4133  # Tallinn
LON_TRUTH = 24.8328

def send_line(line):
    try:
        r = requests.post(WRITE_URL, data=line)
        if r.status_code >= 400:
            print(f"Error {r.status_code}: {r.text}")
        else:
            # Success (Silent unless debug needed)
            pass
    except Exception as e:
        print(f"Conn Error: {e}")

def main():
    print(f"--- SPOOF SIMULATOR V2.1 (Type Fix) ---")
    print(f"Target: {PI_IP}")
    
    for i in range(10):
        now_ns = int(time.time() * 1e9)
        
        # 1. INJECT LOCAL (THE LIE)
        # local_aircraft_state uses INTEGERS for altitude (verified in schema)
        tags_loc = f"icao24={FAKE_ICAO},callsign=GHOST01,host=spoof_injector,source=LocalReadsb"
        fields_loc = (
            f"lat={LAT_LOCAL},"
            f"lon={LON_LOCAL},"
            f"alt_baro_ft=25000i,"       # Integer (Correct for Local)
            f"gs_knots=250.0,"
            f"nav_altitude_mcp_ft=25000i," 
            f"nic=8i,"                   
            f"rc=186i,"                  
            f"rssi=-10.5"                
        )
        send_line(f"local_aircraft_state,{tags_loc} {fields_loc} {now_ns}")

        # 2. INJECT TRUTH (THE REALITY)
        # global_aircraft_state uses FLOATS for altitude (Correction applied here!)
        tags_glob = f"icao24={FAKE_ICAO},callsign=GHOST01,origin_country=FI,source=OpenSkyNetwork"
        fields_glob = (
            f"lat={LAT_TRUTH},"
            f"lon={LON_TRUTH},"
            f"alt_baro_ft=25000.0,"      # Float (Correct for Global)
            f"gs_knots=248.0,"
            f"origin_data=\"GlobalTruth\""
        )
        send_line(f"global_aircraft_state,{tags_glob} {fields_glob} {now_ns}")
        
        print(f"[{i+1}/10] Injected: {FAKE_ICAO}")
        time.sleep(1) 

    print("--- INJECTION COMPLETE ---")

if __name__ == "__main__":
    main()
