import requests
import time
import os
from datetime import datetime

# --- Configuration ---
# FIXED: Using RPi4's actual IP address for JSON source (data/ files)
READSB_HOST = "http://192.168.1.152:8080"
READSB_AIRCRAFT_URL = f"{READSB_HOST}/data/aircraft.json"

# FIXED: InfluxDB runs on RPi5 (Central Server) at localhost
INFLUX_HOST = "http://127.0.0.1:8086"
INFLUX_DB = "readsb" 
INFLUX_WRITE_URL = f"{INFLUX_HOST}/write?db={INFLUX_DB}"

# Measurement name for individual aircraft positions/states
MEASUREMENT = "local_aircraft_state" 

# Time interval for fetching data (must be fast to capture movement, e.g., 1 second)
FETCH_INTERVAL = 1 


def fetch_and_write_aircraft_states():
    """Fetches the list of aircraft from readsb (on RPi4) and writes each one as a point to InfluxDB (on RPi5)."""
    
    # 1. Fetch Dynamic Aircraft List Data
    try:
        response = requests.get(READSB_AIRCRAFT_URL, timeout=2) 
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching aircraft list from RPi4: {e}. Skipping write cycle.")
        return

    # 2. Process the 'aircraft' array
    aircraft_list = data.get('aircraft', [])
    line_protocol_lines = []
    
    # Use the 'now' timestamp provided by the readsb JSON (in seconds)
    base_timestamp = int(data.get('now', time.time()) * 1e9) 

    for ac in aircraft_list:
        if 'hex' in ac and 'lat' in ac and 'lon' in ac:
            icao24 = ac['hex'].lower()
            callsign = ac.get("flight", "N/A").strip()

            # --- FIELD VALUE CLEANUP (Crucial for fixing 'groundi' error) ---
            alt_value = ac.get('alt_baro', 0)
            
            # Check if altitude is a non-numeric string (like "ground" or "unknown")
            if isinstance(alt_value, str):
                if alt_value.lower() == 'ground' or alt_value.lower() == 'unknown':
                    # Set altitude to 0 (integer) and vertical rate to 0 (integer)
                    alt_field = f"alt_baro_ft=0i"
                    v_rate_field = f"v_rate_fpm=0i"
                else:
                    # Fallback for non-standard string, treat as 0
                    alt_field = f"alt_baro_ft=0i"
                    v_rate_field = f"v_rate_fpm=0i"
            else:
                # Value is numeric, append 'i' for integer field type
                alt_field = f"alt_baro_ft={int(alt_value)}i"
                v_rate_field = f"v_rate_fpm={ac.get('baro_rate', 0)}i"
            # --- END FIELD VALUE CLEANUP ---
            
            # --- Tags (Indexed fields for querying and grouping) ---
            tags = f"icao24={icao24},callsign={callsign}"
            line_start = f"{MEASUREMENT},{tags}"

            # --- Fields (Values recorded at the timestamp) ---
            fields = [
                f"lat={ac.get('lat')}",
                f"lon={ac.get('lon')}",
                alt_field,                      # Use cleaned altitude field
                f"gs_knots={ac.get('gs', 0.0)}",          
                f"track={ac.get('track', 0.0)}",          
                v_rate_field,                   # Use cleaned vertical rate field
                f'origin_data="LocalReadsb"'              
            ]
            
            # Combine everything into a Line Protocol string
            line = f"{line_start} {','.join(fields)} {base_timestamp}"
            line_protocol_lines.append(line)


    # 3. Write to InfluxDB
    if line_protocol_lines:
        write_data = "\n".join(line_protocol_lines)
        try:
            influx_response = requests.post(
                INFLUX_WRITE_URL, 
                data=write_data.encode('utf-8'), 
                headers={'Content-Type': 'text/plain'},
                timeout=5
            )
            influx_response.raise_for_status()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Wrote {len(line_protocol_lines)} local aircraft state vectors.")

        except requests.exceptions.HTTPError as err:
            print(f"InfluxDB HTTP Error: {err}. Response text: {err.response.text}")
        except Exception as e:
            print(f"An unexpected error occurred during InfluxDB write: {e}")


def main_loop():
    """Main loop for readsb position data fetching and writing."""
    print(f"Starting readsb aircraft position feeder. Target: {READSB_AIRCRAFT_URL}")

    while True:
        start_time = time.time()
        
        fetch_and_write_aircraft_states()

        # Wait for the next interval
        time_spent = time.time() - start_time
        wait_time = max(0, FETCH_INTERVAL - time_spent)
        time.sleep(wait_time)


if __name__ == "__main__":
    main_loop()
