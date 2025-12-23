#!/usr/bin/env python3
"""
Script: restore_balcony.py
Version: 2.1.0 (Fix: Uses 'env add' instead of 'set')
Description: 
    Restores the identity variables to the Balcony node.
"""

import subprocess
import sys
import time

# --- CONFIGURATION ---
# REPLACE THIS with the UUID of your active Balcony device
TARGET_UUID = "f388f9e085d06aa80840897e1efdad7f" 

VARIABLES = {
    # --- IDENTITY ---
    "SENSOR_ID": "keimola-balcony",
    "SENSOR_ROLE": "scout",
    
    # --- LOCATION ---
    "LAT": "60.31955",
    "LON": "24.83084",
    "ALT": "100",
    
    # --- FEEDER KEYS ---
    "PIAWARE_FEEDER_ID": "159650a4-b275-4411-9d62-ef7193d61586",
    "FR24_KEY": "2862e2d7873b4db7",
    "AIRNAV_RADAR_KEY": "EXTRPI692312",
    "PLANEFINDER_SHARECODE": "6930b359bf63a",
    "OPENSKY_SERIAL": "-405630940",
    "OPENSKY_USERNAME": "rwiren2",
    
    # --- HARDWARE ---
    "GPSD_OPTIONS": "-N -n -G", 
    "SERIAL_DEVICE": "ttyUSB0",
    "BAUD_RATE": "115200",
    
    # --- NETWORK ---
    "READSB_NET_ENABLE": "true",
    "READSB_NET_CONNECTOR": "192.168.1.134,30004,beast_out",
    "GNSS_TYPE": "standard" 
}

def set_variable(uuid, key, value):
    print(f"   -> Setting {key}...")
    # FIX: Changed 'set' to 'add'
    cmd = ["balena", "env", "add", key, str(value), "--device", uuid]
    try:
        # We capture output to check for "Variable already exists" errors
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode == 0:
            print("      ✅ OK")
        elif "already exists" in proc.stderr:
            print("      ⚠️  Exists (Skipping)")
        else:
            print(f"      ❌ FAILED: {proc.stderr.strip()}")
            
    except Exception as e:
        print(f"      ❌ ERROR: {e}")

def main():
    print("=======================================")
    print("   KEIMOLA-BALCONY RESTORATION v2.1")
    print("=======================================")
    
    if TARGET_UUID == "REPLACE_WITH_NEW_UUID":
        print("❌ ERROR: You must edit the script and set TARGET_UUID first!")
        sys.exit(1)

    print(f"Target: {TARGET_UUID}")
    print("-" * 40)
    
    confirm = input("Are you sure? (y/n): ")
    if confirm.lower() != 'y':
        sys.exit(0)

    for key, value in VARIABLES.items():
        set_variable(TARGET_UUID, key, value)
        time.sleep(1) 

    print("-" * 40)
    print("✅ DONE. Please restart the device.")

if __name__ == "__main__":
    main()
