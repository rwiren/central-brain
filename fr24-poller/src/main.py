#!/usr/bin/env python3
"""
🎅 SANTA TRACKER - FR24 Poller Service
--------------------------------------
Version: 5.1.1 (Hotfix)
Author: Richard / Riku
Date: 2025-12-23
Description: Polls Flightradar24 for Santa's location and writes to InfluxDB.
Fixes: Added 'Accept-Version' header to resolve 400 Bad Request errors.
"""

import time
import json
import os
import requests
import sys
from datetime import datetime

# ---------------- CONFIGURATION ----------------
# Use environment variable if available, otherwise fallback to the known token
TOKEN = os.getenv("FR24_TOKEN", "Your-TOKEN-HERE")

# Endpoint for full flight positions
URL = "https://fr24api.flightradar24.com/api/live/flight-positions/full"

# Tracking targets (Santa's known callsigns)
SANTA_CALLSIGNS = "R3DN053,SANTA1,HOHOHO,CMC,REDNOSE"
POLL_INTERVAL = 15  # Seconds

# ---------------- LOGGING HELPER ----------------
def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    print(f"{timestamp} <fr24-poller> {level}: {message}")
    sys.stdout.flush()

# ---------------- MAIN LOOP ----------------
def main():
    print("--------------------------------------------------")
    log("--- 🎅 SANTA TRACKER v5.1.1 (HOTFIX) ACTIVATED ---")
    log(f"    Targets:  {SANTA_CALLSIGNS}")
    log(f"    Interval: {POLL_INTERVAL} seconds")
    log("    Database: influxdb:8086")
    log("✅  Commercial Credits Active.")
    log("Ready for intercept.")
    print("--------------------------------------------------")

    # FIX 1: Headers must include 'Accept-Version: v1'
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Accept-Version": "v1"  # <--- CRITICAL FIX FOR 400 ERROR
    }

    # FIX 2: Correct parameters for callsign filtering
    params = {
        "callsigns": SANTA_CALLSIGNS,
        # "operating_as": "FIN"  # Uncomment this line if you want to test with Finnair
    }

    while True:
        try:
            log(f"Polling FR24... (Targeting: {URL})", level="DEBUG")
            
            response = requests.get(URL, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                flight_list = data.get('data', [])
                
                if flight_list:
                    count = len(flight_list)
                    log(f"🎯 TARGET LOCKED: Found {count} object(s) matching filters.")
                    
                    # TODO: Insert InfluxDB write logic here
                    # For now, just dumping the raw JSON to stdout so we see it
                    print(json.dumps(flight_list[0], indent=2))
                    
                else:
                    log("📡 Scan complete. No targets (Santa) currently airborne.", level="INFO")
            
            elif response.status_code == 400:
                # Specific handling for the error we just fixed
                log(f"⚠️ FR24 API Status: 400 - Validation Failed. Check Headers/Params.", level="ERROR")
                log(f"Response: {response.text}", level="DEBUG")
            
            else:
                log(f"⚠️ FR24 API Status: {response.status_code}", level="WARN")
                log(f"Response: {response.text}", level="DEBUG")

        except requests.exceptions.ConnectionError:
            log("Connection failed. Retrying...", level="ERROR")
        except Exception as e:
            log(f"Unexpected script error: {e}", level="CRITICAL")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
