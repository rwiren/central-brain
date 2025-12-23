#!/usr/bin/env python3
"""
System: Central Brain - Single Day Raw Dumper
Script: dump_single_day_raw.py
Description: Connects to RPi5 and dumps ALL measurements for a specific 
             24-hour window into InfluxDB Line Protocol (.lp) format.
             Perfect for sharing a 'Raw Data Sample' with the AI team.

             Target Date: 2025-11-30 (The Golden Day)
"""

import sys
import time
import datetime
from influxdb import InfluxDBClient

# ================= Configuration =================
CONF = {
    'host': '192.168.1.134', 
    'port': 8086,
    'user': 'admin',
    'pass': 'password',
    'batch_size': 5000,
    'target_date': '2025-11-30', # <--- The day you want to share
    'output_file': 'raw_dump_2025-11-30.lp'
}

def connect_db():
    print(f"[INFO] Connecting to {CONF['host']}...")
    client = InfluxDBClient(CONF['host'], CONF['port'], CONF['user'], CONF['pass'])
    
    if hasattr(client, '_headers'):
        client._headers['Accept'] = 'application/json'
        
    try:
        client.ping()
        print("[OK] Connection successful.")
        return client
    except Exception as e:
        print(f"[FATAL] Could not connect: {e}")
        sys.exit(1)

def escape_tag(val):
    return str(val).replace(" ", "\ ").replace(",", "\,").replace("=", "\=")

def escape_field(val):
    if isinstance(val, str):
        escaped = val.replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(val, int):
        return f"{val}i"
    return str(val)

def main():
    client = connect_db()
    
    # Calculate Time Window
    start_time = f"{CONF['target_date']}T00:00:00Z"
    end_time = f"{CONF['target_date']}T23:59:59Z"
    print(f"[INFO] Target Window: {start_time} to {end_time}")

    print("\n[STEP 1] Scanning for Databases...")
    dbs = client.get_list_database()
    ignore_dbs = ['_internal']
    target_dbs = [d['name'] for d in dbs if d['name'] not in ignore_dbs]
    
    total_records = 0
    
    with open(CONF['output_file'], 'w', encoding='utf-8') as f:
        for db in target_dbs:
            print(f"\n[STEP 2] Processing Database: '{db}'")
            client.switch_database(db)
            
            measurements = client.get_list_measurements()
            print(f" > Found {len(measurements)} tables.")
            
            for m in measurements:
                table = m['name']
                print(f"   - Dumping {table}...", end='', flush=True)
                
                # Query specific time range
                query = (f"SELECT * FROM \"{table}\" "
                         f"WHERE time >= '{start_time}' AND time <= '{end_time}'")
                
                table_count = 0
                try:
                    result_gen = client.query(query, chunked=True, chunk_size=CONF['batch_size'])
                    
                    for result in result_gen:
                        raw_points = list(result.get_points())
                        for p in raw_points:
                            ts = p.pop('time', None)
                            
                            # Convert ISO time to nanoseconds for Line Protocol
                            ns = 0
                            if ts and 'T' in ts:
                                try:
                                    # Handle fractional seconds if present (e.g. .123Z)
                                    # Simple parsing:
                                    if '.' in ts:
                                        base_time, fract = ts.rstrip('Z').split('.')
                                        t_obj = time.strptime(base_time, "%Y-%m-%dT%H:%M:%S")
                                        # Reconstruct with nanosecond precision approximation
                                        ns = int(time.mktime(t_obj) * 1e9) + int(float(f"0.{fract}") * 1e9)
                                    else:
                                        t_obj = time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                                        ns = int(time.mktime(t_obj) * 1e9)
                                except:
                                    # Fallback
                                    ns = int(time.time() * 1e9)
                            
                            # Build Line Protocol String
                            field_set = []
                            for k, v in p.items():
                                if v is not None:
                                    key_str = escape_tag(k)
                                    val_str = escape_field(v)
                                    field_set.append(f"{key_str}={val_str}")
                            
                            if field_set:
                                line = f"{table} {','.join(field_set)} {ns}\n"
                                f.write(line)
                                table_count += 1
                                
                    print(f" Done. ({table_count} records)")
                    total_records += table_count
                    
                except Exception as e:
                    print(f" [FAIL] Error: {e}")

    print(f"\n[SUCCESS] Single Day Dump Complete.")
    print(f"  - Total Records: {total_records}")
    print(f"  - Saved to: {CONF['output_file']}")
    print("  -> Share this .lp file with your team alongside the CSVs.")

if __name__ == "__main__":
    main()
