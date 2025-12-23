#!/usr/bin/env python3
"""
System: Central Brain - Blind Raw Data Dumper
Script: dump_complete_raw.py
Description: Connects to RPi5, discovers ALL databases/tables, and dumps 
             every single data point to a text file (Line Protocol).
             This 'fixes' extraction by ignoring filters/dates.
"""

import sys
import time
import socket
from influxdb import InfluxDBClient
from requests.exceptions import ConnectionError

# ================= Configuration =================
CONF = {
    'host': '192.168.1.134', # RPi5 IP
    'port': 8086,
    'user': 'admin',         # Default for many setups
    'pass': 'password',      # Default for many setups
    'batch_size': 5000,
    'output_file': 'central_brain_full_dump.lp'
}

def connect_db():
    print(f"[INFO] Connecting to {CONF['host']}...")
    client = InfluxDBClient(CONF['host'], CONF['port'], CONF['user'], CONF['pass'])
    
    # CRITICAL FIX: Force JSON header to prevent 'msgpack' errors on RPi
    if hasattr(client, '_headers'):
        client._headers['Accept'] = 'application/json'
        
    try:
        # Ping to verify auth/connection
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
        return f'"{val.replace("\"", "\\\"")}"'
    return f"{val}i" if isinstance(val, int) else str(val)

def main():
    client = connect_db()
    
    # 1. Get ALL Databases
    print("\n[STEP 1] Scanning for Databases...")
    dbs = client.get_list_database()
    ignore_dbs = ['_internal'] # Skip internal Influx stats
    target_dbs = [d['name'] for d in dbs if d['name'] not in ignore_dbs]
    
    if not target_dbs:
        print("[ERROR] No user databases found!")
        sys.exit(1)
        
    print(f" > Found DBs: {target_dbs}")
    
    with open(CONF['output_file'], 'w', encoding='utf-8') as f:
        
        # 2. Iterate through every DB
        for db in target_dbs:
            print(f"\n[STEP 2] Processing Database: '{db}'")
            client.switch_database(db)
            
            measurements = client.get_list_measurements()
            print(f" > Found {len(measurements)} tables.")
            
            for m in measurements:
                table = m['name']
                print(f"   - Dumping table: {table}...", end='', flush=True)
                
                # 3. Dump Everything (No Date Filter)
                # We simply select *
                query = f'SELECT * FROM "{table}"'
                points_count = 0
                
                try:
                    # Chunked query to prevent RPi crash
                    result_gen = client.query(query, chunked=True, chunk_size=CONF['batch_size'])
                    
                    for result in result_gen:
                        raw_points = list(result.get_points())
                        for p in raw_points:
                            # Construct Line Protocol: measurement tag=v field=v timestamp
                            # Since we get a flat dict, we treat non-time/non-tag as fields
                            ts = p.pop('time', None)
                            
                            # Convert ISO time to nano-seconds (approx)
                            if ts and 'T' in ts:
                                t_obj = time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                                ns = int(time.mktime(t_obj) * 1e9)
                            else:
                                ns = int(time.time() * 1e9)

                            # Format fields
                            field_set = []
                            for k, v in p.items():
                                if v is not None:
                                    field_set.append(f"{escape_tag(k)}={escape_field(v)}")
                            
                            if field_set:
                                line = f"{table} {','.join(field_set)} {ns}\n"
                                f.write(line)
                                points_count += 1
                                
                    print(f" Done. ({points_count} records)")
                    
                except Exception as e:
                    print(f" [FAIL] Error reading {table}: {e}")

    print(f"\n[SUCCESS] Dump Complete. Saved to: {CONF['output_file']}")

if __name__ == "__main__":
    main()
