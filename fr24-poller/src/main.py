import requests
import time
import os
import sys
from datetime import datetime

# ==============================================================================
# Script: main.py (FR24 Poller)
# Service: Santa Tracker (Holiday Edition)
# Version: 5.1.0 (Santa Turbo Mode)
# Description: 
#   - High-Speed Polling (15s) using Commercial API Credits.
#   - Tracks 'SLEI' type aircraft and specific holiday callsigns.
#   - Captures Physics (Vertical Rate) for AI anomaly training.
#   - Writes to InfluxDB using "Level 4" Schema (Global Truth).
# ==============================================================================

# --- DATABASE CONFIGURATION ---
INFLUX_HOST = os.getenv("INFLUX_HOST", "influxdb")
INFLUX_PORT = int(os.getenv("INFLUX_PORT", 8086))
INFLUX_DB = "readsb"
WRITE_URL = f"http://{INFLUX_HOST}:{INFLUX_PORT}/write?db={INFLUX_DB}"

# --- FR24 API CONFIGURATION ---
# Your Commercial API Token (Must be set in Balena Variables)
API_TOKEN = os.getenv("FR24_API_TOKEN") 

# Polling Interval
# 15s = High resolution for Physics Engine (Uses ~5,700 queries/day)
# 60s = Economy mode
FETCH_INTERVAL = 15 

# --- TARGET IDENTIFIERS ---
# Known identifiers for Santa's Sleigh on Flightradar24
# SANTA1, R3DN053 (Red Nose), HOHOHO, CMC (Christmas Magic), REDNOSE
SANTA_CALLSIGNS = "SANTA1,R3DN053,HOHOHO,CMC,REDNOSE"

def write_to_influx(lines):
    """Writes a batch of InfluxDB Line Protocol strings."""
    if not lines: return
    try:
        w = requests.post(WRITE_URL, data="\n".join(lines), timeout=5)
        if w.status_code >= 400:
            print(f"[InfluxDB] Write Error: {w.status_code} - {w.text}")
        else:
            print(f"[InfluxDB] Successfully logged {len(lines)} holiday positions.")
    except Exception as e:
        print(f"[InfluxDB] Connection Error: {e}")

def fetch_santa():
    """Queries FR24 specifically for Santa's callsigns with rich telemetry."""
    url = "https://fr24api.flightradar24.com/api/live/flight-positions"
    
    headers = {
        "Accept": "application/json"
    }
    
    # 1. Authentication (Credits)
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    else:
        print("⚠️ WARNING: No FR24_API_TOKEN found. Running in restricted mode.")

    # 2. Parameters
    # We ask for specific columns including 'vspeed' for physics analysis
    params = {
        "callsign": SANTA_CALLSIGNS,
        "columns": "ident,lat,lon,alt,speed,heading,squawk,type,reg,orig,dest,vspeed"
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        
        if r.status_code == 200:
            return r.json().get('data', [])
        elif r.status_code == 402:
            print("❌ FR24: Payment Required (Credits Exhausted).")
        elif r.status_code == 401:
            print("❌ FR24: Unauthorized (Invalid Token).")
        else:
            print(f"⚠️ FR24 API Status: {r.status_code}")
            
    except Exception as e:
        print(f"⚠️ Connection Failed: {e}")
    
    return []

def process_sleigh(flights, now_ns):
    """Converts API JSON to InfluxDB Line Protocol (Level 4 Schema)."""
    lines = []
    
    for f in flights:
        # --- 1. Identity Extraction ---
        ident = f.get('ident', 'UNKNOWN')
        reg = f.get('reg', 'N/A')
        # Default to SLEI (Sleigh) if type is missing or generic
        type_code = f.get('type') or 'SLEI' 
        
        # --- 2. Physics Data ---
        lat = f.get('lat')
        lon = f.get('lon')
        alt = f.get('alt', 0)
        speed = f.get('speed', 0)
        heading = f.get('heading', 0)
        # Vertical Speed (Essential for detecting "Magic" takeoffs)
        vert_rate = f.get('vspeed', 0) 
        
        if not lat or not lon: continue

        # --- 3. Tagging (The "Magic" Flags) ---
        # We explicitly tag this so AI models can filter it out as an anomaly.
        tags = (
            f"icao24={ident},"         # Use callsign as ICAO for uniqueness
            f"callsign={ident},"
            f"registration={reg},"
            f"type_code={type_code},"  # SLEI
            f"source=FR24_SantaTracker"
        )
        
        # --- 4. Fields (Level 4 Schema) ---
        # Note the 'i' suffix on integers for InfluxDB strict typing
        fields = (
            f"lat={float(lat)},"
            f"lon={float(lon)},"
            f"alt_baro_ft={int(alt)}i,"
            f"gs_knots={float(speed)},"
            f"track={float(heading)},"
            f"vert_rate_fpm={float(vert_rate)}i," # <--- Physics Engine Input
            f"is_anomaly=true,"       # Flag for Data Scientists
            f"magic_enabled=true,"    # Dashboard flag
            f"origin_data=\"NorthPole\""
        )
        
        lines.append(f"global_aircraft_state,{tags} {fields} {now_ns}")
        
        # Log detection to console for Balena logs
        print(f"🎅 DETECTED: {ident} ({type_code}) | Alt: {alt}ft | VS: {vert_rate} fpm")

    return lines

def main():
    print(f"--- 🎅 SANTA TRACKER v5.1.0 ACTIVATED ---")
    print(f"    Targets:  {SANTA_CALLSIGNS}")
    print(f"    Interval: {FETCH_INTERVAL} seconds (High-Speed)")
    print(f"    Database: {INFLUX_HOST}:{INFLUX_PORT}")
    
    if not API_TOKEN:
        print("⚠️  CRITICAL: Running without Credits! Rate limits may apply.")
    else:
        print("✅  Commercial Credits Active. Ready for intercept.")

    while True:
        try:
            # 1. Hunt for Santa
            flights = fetch_santa()
            
            if flights:
                # 2. Process & Ingest
                now_ns = int(time.time() * 1e9)
                lines = process_sleigh(flights, now_ns)
                write_to_influx(lines)
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                # print(f"[{timestamp}] North Pole Scan: Negative.") 
                # Kept silent to avoid log spam, uncomment if debugging

        except Exception as e:
            print(f"Loop Error: {e}")

        # Sleep interval (15s for Turbo Mode)
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main()
