#!/usr/bin/env python3
"""
System: Central Brain - Blind Raw Data Dumper
Script: dump_complete_raw_v2.py
Description: Connects to RPi5, discovers ALL databases/tables, and dumps 
             every single data point to a text file (Line Protocol).
             
             Changes in v2:
             - Fixed f-string syntax error for compatibility with older Python versions.
             - Improved escaping logic for Line Protocol.

Version: 1.0.1
Author: RW
Date: 2025-12-18
Revision: 2
"""

import sys
import time
import socket
from influxdb import InfluxDBClient

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
    """Escapes tag keys and values."""
    # Tags cannot contain spaces, commas, or equal signs without escaping
    return str(val).replace(" ", "\ ").replace(",", "\,").replace("=", "\=")

def escape_field(val):
    """Escapes field values (Strings must be quoted)."""
    if isinstance(val, str):
        # Move backslash operation outside f-string for Python <3.12 compatibility
        escaped = val.replace('"', '\\"')
        return f'"{escaped}"'
    
    # Integers in InfluxDB Line Protocol need an 'i' suffix
    if isinstance(val, int):
        return f"{val}i"
        
    return str(val)

def main():
    client = connect_db()
    
    # 1. Get ALL Databases
    print("\n[STEP 1] Scanning for Databases...")
    try:
        dbs = client.get_list_database()
    except Exception as e:
        print(f"[FATAL] Failed to list databases: {e}")
        sys.exit(1)

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
                query = f'SELECT * FROM "{table}"'
                points_count = 0
                
                try:
                    # Chunked query to prevent RPi crash
                    result_gen = client.query(query, chunked=True, chunk_size=CONF['batch_size'])
                    
                    for result in result_gen:
                        raw_points = list(result.get_points())
                        for p in raw_points:
                            # Construct Line Protocol: measurement tag=v field=v timestamp
                            # Since we get a flat dict from SELECT *, we treat everything 
                            # (except 'time') as fields to ensure data survival.
                            ts = p.pop('time', None)
                            
                            # Convert ISO time to nano-seconds (approx)
                            ns = 0
                            if ts and 'T' in ts:
                                try:
                                    t_obj = time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                                    ns = int(time.mktime(t_obj) * 1e9)
                                except ValueError:
                                    # Handle fractional seconds if present
                                    ns = int(time.time() * 1e9)
                            else:
                                ns = int(time.time() * 1e9)

                            # Format fields
                            field_set = []
                            for k, v in p.items():
                                if v is not None:
                                    # We use escape_tag for keys (standard)
                                    # We use escape_field for values
                                    key_str = escape_tag(k)
                                    val_str = escape_field(v)
                                    field_set.append(f"{key_str}={val_str}")
                            
                            if field_set:
                                # Write line: measurement field=val,field=val timestamp
                                # Note: In a raw blind dump, we treat all columns as fields 
                                # to avoid schema mismatch logic.
                                line = f"{table} {','.join(field_set)} {ns}\n"
                                f.write(line)
                                points_count += 1
                                
                    print(f" Done. ({points_count} records)")
                    
                except Exception as e:
                    print(f" [FAIL] Error reading {table}: {e}")

    print(f"\n[SUCCESS] Dump Complete. Saved to: {CONF['output_file']}")

if __name__ == "__main__":
    main()
