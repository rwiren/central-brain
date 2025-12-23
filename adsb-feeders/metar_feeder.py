import requests
import time
import os
import re

# ==============================================================================
# Script: metar_feeder.py
# Service: Local Weather (METAR)
# Version: 1.0.1 (Restoration)
# Description: Fetches real-time aviation weather for EFHK (Helsinki).
# ==============================================================================

# Configuration
INFLUX_HOST = os.getenv("INFLUX_HOST", "http://influxdb:8086")
INFLUX_DB = os.getenv("INFLUX_DB", "readsb")
INFLUX_WRITE_URL = f"{INFLUX_HOST}/write?db={INFLUX_DB}"

STATION = "EFHK"
METAR_URL = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{STATION}.TXT"

def parse_metar(raw):
    data = {
        "station": STATION,
        "raw_metar": f'"{raw.strip()}"'
    }
    
    # 1. Temp/Dewpoint (M01/M02)
    temp_match = re.search(r'\s(M?\d{2})/(M?\d{2})\s', raw)
    if temp_match:
        t_str, d_str = temp_match.groups()
        data["temperature_c"] = float(t_str.replace('M', '-'))
        data["dewpoint_c"] = float(d_str.replace('M', '-'))

    # 2. Pressure (Q1008)
    qnh_match = re.search(r'\sQ(\d{4})', raw)
    if qnh_match:
        data["pressure_hpa"] = float(qnh_match.group(1))

    # 3. Wind
    wind_match = re.search(r'\s(\d{3})(\d{2})G?(\d{2})?KT', raw)
    if wind_match:
        data["wind_dir_deg"] = float(wind_match.group(1))
        data["wind_speed_kt"] = float(wind_match.group(2))

    # 4. Visibility
    vis_match = re.search(r'\s(\d{4})\s', raw)
    if vis_match:
        data["visibility_miles"] = float(vis_match.group(1)) / 1609.34

    return data

def main():
    print(f"[METAR] Starting Weather Feeder for {STATION}...")
    
    last_raw = ""
    
    while True:
        try:
            r = requests.get(METAR_URL, timeout=10)
            if r.status_code == 200:
                lines = r.text.strip().split('\n')
                if len(lines) >= 2:
                    current_metar = lines[1]
                    
                    if current_metar != last_raw:
                        last_raw = current_metar
                        parsed = parse_metar(current_metar)
                        
                        tags = f"station={parsed['station']}"
                        fields = []
                        for k, v in parsed.items():
                            if k != "station":
                                fields.append(f"{k}={v}")
                        
                        line = f"weather_local,{tags} {','.join(fields)}"
                        
                        requests.post(INFLUX_WRITE_URL, data=line)
                        print(f"[METAR] Updated: {current_metar}")
                    
        except Exception as e:
            print(f"[METAR] Error: {e}")
            
        time.sleep(300)

if __name__ == "__main__":
    main()
