"""
Script: inspect_sensor_battle.py
Version: 1.4.0 (The Final Referee)
Description: 
    Validates Sensor Performance by correlating:
    1. GNSS Accuracy (from gps-logger)
    2. RF Range & Volume (from battle_engine)
"""

import time
from influxdb import InfluxDBClient

# --- CONFIGURATION ---
INFLUX_HOST = "192.168.1.134" 
INFLUX_PORT = 8086
INFLUX_DB   = "readsb"

def get_stat(client, measurement, host, field, func="last", time_window="10m"):
    """Fetches a single statistic from InfluxDB."""
    query = f"""
        SELECT {func}("{field}") 
        FROM "{measurement}" 
        WHERE "host" = '{host}' 
        AND time > now() - {time_window}
    """
    try:
        points = list(client.query(query).get_points())
        if points:
            val = points[0][func]
            if isinstance(val, float): return round(val, 2)
            return val
    except:
        pass
    return None

def main():
    print(f"--- CONNECTING TO BRAIN [{INFLUX_HOST}] ---")
    try:
        client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
        client.switch_database(INFLUX_DB)
    except Exception as e:
        print(f"[CRITICAL] Database Connection Failed: {e}")
        return

    print(">>> Scanning Active Sensors (Last 10m)...")
    hosts = set()
    try:
        # Find all hosts reporting either GPS or Battle Stats
        q1 = client.query('SHOW TAG VALUES FROM "gps_tpv" WITH KEY = "host" WHERE time > now() - 10m')
        q2 = client.query('SHOW TAG VALUES FROM "rf_battle_stats" WITH KEY = "host" WHERE time > now() - 10m')
        for p in q1.get_points(): hosts.add(p['value'])
        for p in q2.get_points(): hosts.add(p['value'])
    except Exception as e:
        print(f"[ERROR] Scan Failed: {e}")
        return

    # Header
    print("-" * 110)
    print(f"{'SENSOR':<20} | {'TYPE':<10} | {'ACCURACY':<10} | {'SATS':<5} || {'MAX RANGE':<10} | {'MSG/SEC':<10} | {'STATUS'}")
    print("-" * 110)

    for host in sorted(hosts):
        # 1. Fetch GNSS Metrics
        # We check multiple fields because different gpsd versions use different names
        status = get_stat(client, "gps_tpv", host, "status") or 0
        mode   = get_stat(client, "gps_tpv", host, "mode") or 0
        acc    = get_stat(client, "gps_tpv", host, "epx", "mean")
        sats   = get_stat(client, "gps_tpv", host, "satellites_used", "last") or 0

        # 2. Fetch Battle Metrics
        rnge   = get_stat(client, "rf_battle_stats", host, "max_range_nm", "max") or "-"
        act    = get_stat(client, "rf_battle_stats", host, "activity_score", "mean") or "-"

        # 3. Determine Sensor Type (The "Truth" Logic)
        type_str = "NO FIX"
        
        if mode == 3:
            type_str = "STD 3D"
            # If status is 4 (Float) or 5 (Fixed), it's RTK
            if status == 4: 
                type_str = "FLOAT"
            elif status == 5: 
                type_str = "FIXED"
            # Fallback: If status is 3 (GPSD default) but accuracy is insane (<0.2m), it's Fixed
            elif status == 3 and acc is not None and acc < 0.2:
                type_str = "FIXED"

        # 4. Format & Print
        acc_str = f"{acc}m" if acc is not None else "-"
        
        # Calculate approximate Msg/Sec from Activity Score (Score = Count * 10 in 15s window)
        # Msg/Sec ~= Score / 150? No, Score was Raw Count * 10. 
        # Let's just print the raw score for relative comparison.
        
        print(f"{host:<20} | {type_str:<10} | {acc_str:<10} | {int(sats):<5} || {str(rnge):<10} | {str(act):<10} | Active")

    print("-" * 110)
    print("LEGEND: FIXED (<0.2m) | FLOAT (<1.0m) | STD 3D (>3.0m)")

if __name__ == "__main__":
    main()
