#!/usr/bin/env python3
# ==============================================================================
# Script: battle_engine.py
# Role:   Logic Engine (Central Brain)
# Version: 3.2.0 (Fix: Host Tag Extraction)
# ==============================================================================

import time
import math
import datetime
import os
from influxdb import InfluxDBClient

DB_HOST = os.getenv("INFLUX_HOST_NAME", "influxdb") 
DB_PORT = 8086
DB_NAME = 'readsb'

# Reference Coordinates (Keimola)
REF_LAT = 60.319555
REF_LON = 24.830819

def haversine(lat1, lon1, lat2, lon2):
    try:
        R = 3440.065 # Radius of earth in NM
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    except:
        return 0.0

class BattleRef:
    def __init__(self):
        print(f"[BATTLE] Initializing Logic Engine v3.2.0...")
        self.client = InfluxDBClient(host=DB_HOST, port=DB_PORT)
        while True:
            try:
                self.client.switch_database(DB_NAME)
                print("[SUCCESS] Connected to Database.")
                break
            except Exception as e:
                print(f"[WAIT] Database not ready: {e}")
                time.sleep(5)

    def run(self):
        print("[RUNNING] Calculating Battle Stats...")
        while True:
            try:
                # Query last known position for every ICAO, grouped by host
                query = """
                    SELECT last("lat") as lat, last("lon") as lon, last("alt_baro_ft") as alt
                    FROM "local_aircraft_state" 
                    WHERE time > now() - 15s 
                    GROUP BY "icao24", "host"
                """
                results = self.client.query(query)
                
                stats = {} 

                # Iterate through the ResultSet
                # keys are (measurement, tags) tuples
                for (name, tags), points in results.items():
                    host = tags.get('host', 'unknown')
                    
                    # Process points
                    for p in points:
                        lat = p.get('lat')
                        lon = p.get('lon')
                        alt = p.get('alt')
                        
                        if not lat or not lon: continue

                        if host not in stats:
                            stats[host] = {'count': 0, 'max_range': 0.0, 'ground': 0, 'low': 0, 'mid': 0, 'high': 0}

                        dist = haversine(REF_LAT, REF_LON, lat, lon)
                        if dist > stats[host]['max_range']:
                            stats[host]['max_range'] = dist

                        stats[host]['count'] += 1
                        
                        if alt is None or alt == 0: stats[host]['ground'] += 1
                        elif alt < 10000: stats[host]['low'] += 1
                        elif alt < 30000: stats[host]['mid'] += 1
                        else: stats[host]['high'] += 1

                # Write Stats
                timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                points_to_write = []
                
                for host, d in stats.items():
                    points_to_write.append({
                        "measurement": "rf_battle_stats",
                        "tags": { "host": host, "role": "sensor" },
                        "time": timestamp,
                        "fields": {
                            "total_count": int(d['count']),
                            "max_range_nm": float(d['max_range']),
                            "ground_count": int(d['ground']),
                            "activity_score": int(d['count'] * 10) 
                        }
                    })

                if points_to_write:
                    self.client.write_points(points_to_write)
            
            except Exception as e:
                print(f"[ERROR] Loop Failed: {e}")

            time.sleep(10)

if __name__ == "__main__":
    eng = BattleRef()
    eng.run()
