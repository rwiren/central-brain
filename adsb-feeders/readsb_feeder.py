import requests
import time
import os
from datetime import datetime

# --- Configuration ---
# FIXED: Using RPi4's actual IP address for JSON source
# The Python script on RPi5 fetches the JSON web data directly from the RPi4's web server.
READSB_HOST = "http://192.168.1.152:8080"
READSB_STATS_URL = f"{READSB_HOST}/data/stats.json"
READSB_RECEIVER_URL = f"{READSB_HOST}/data/receiver.json"

# FIXED: InfluxDB runs on RPi5 (Central Server) at localhost
INFLUX_HOST = "http://127.0.0.1:8086"
INFLUX_DB = "readsb" 
INFLUX_WRITE_URL = f"{INFLUX_HOST}/write?db={INFLUX_DB}"

# Measurement name for receiver performance stats
MEASUREMENT = "local_performance" 

# Time interval for fetching data (matching the OpenSky feeder)
FETCH_INTERVAL = 15 


def fetch_and_write_stats():
    """Fetches stats from readsb (on RPi4) and writes performance metrics to InfluxDB (on RPi5)."""
    
    # 1. Fetch Static Receiver Metadata (Lat/Lon)
    try:
        rx_response = requests.get(READSB_RECEIVER_URL, timeout=5)
        rx_response.raise_for_status()
        rx_data = rx_response.json()
        # NOTE: We read the lat/lon from the RPi4's receiver JSON, not the RPi5's ENV variables
        receiver_lat = rx_data.get("lat", 0.0)
        receiver_lon = rx_data.get("lon", 0.0)
    except Exception as e:
        print(f"Error fetching receiver config from RPi4: {e}. Using default 0.0.")
        receiver_lat, receiver_lon = 0.0, 0.0
        
    # 2. Fetch Dynamic Stats Data
    try:
        stats_response = requests.get(READSB_STATS_URL, timeout=5)
        stats_response.raise_for_status()
        stats_data = stats_response.json()
    except Exception as e:
        print(f"Error fetching stats from RPi4: {e}. Skipping write cycle.")
        return

    # 3. Process the 'latest' interval data
    latest = stats_data.get('latest', {})
    
    # InfluxDB Line Protocol: measurement,tags field=value timestamp

    # Tags for filtering/grouping
    tags = f"host=readsb_rpi4,lat={receiver_lat},lon={receiver_lon}"
    line_start = f"{MEASUREMENT},{tags}"

    # Fields (The actual performance metrics)
    fields = [
        f"messages={latest.get('messages', 0)}i", 
        f"cpu_sec={latest.get('cpu_seconds', 0.0)}",
        f"signal_db={latest.get('signal', 0.0)}",
        f"airborne_msg={latest.get('accepted', [0])[0]}i", 
        f"strong_signals={latest.get('strong_signals', 0)}i",
        f"messages_total_lifetime={stats_data.get('total', {}).get('messages', 0)}i"
    ]
    
    # Timestamp (Using current time in nanoseconds for InfluxDB consistency)
    timestamp = int(time.time() * 1e9) 
    
    line_data = f"{line_start} {','.join(fields)} {timestamp}"

    # 4. Write to InfluxDB 1.8 using the /write endpoint
    try:
        influx_response = requests.post(
            INFLUX_WRITE_URL, 
            data=line_data.encode('utf-8'), 
            headers={'Content-Type': 'text/plain'},
            timeout=5
        )
        influx_response.raise_for_status()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Wrote readsb stats successfully.")

    except requests.exceptions.HTTPError as err:
        print(f"InfluxDB HTTP Error: {err}. Response text: {err.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during InfluxDB write: {e}")


def main_loop():
    """Main loop for readsb data fetching and writing."""
    print(f"Starting readsb data feeder. Target: {READSB_HOST}")
    print(f"Writing to InfluxDB at: {INFLUX_WRITE_URL}")

    while True:
        start_time = time.time()
        
        fetch_and_write_stats()

        # Wait for the next interval
        time_spent = time.time() - start_time
        wait_time = max(0, FETCH_INTERVAL - time_spent)
        time.sleep(wait_time)


if __name__ == "__main__":
    main_loop()
