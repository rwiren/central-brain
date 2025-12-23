#!/usr/bin/env python3
"""
Script: debug_balcony.py
Description: Remote diagnostics for Keimola-Balcony Piaware issues.
"""
import subprocess
import sys

# UUID for Keimola-Balcony (from your logs)
TARGET_UUID = "f388f9e085d06aa80840897e1efdad7f"

def run_remote(command, service="piaware"):
    print(f"👉 Running: {command}...")
    cmd = ["balena", "ssh", TARGET_UUID, service, "--", command]
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        print(f"❌ Failed: {e}")
    print("-" * 40)

def main():
    print("--- BALCONY DIAGNOSTICS ---")
    
    # 1. Check if variable is visible to the OS
    print("\n[1] Checking Environment Variable:")
    run_remote("env | grep FEEDER_ID")

    # 2. Check Piaware Status
    print("\n[2] Checking Piaware Status:")
    run_remote("piaware-status")

    # 3. Check Config File
    print("\n[3] Checking Config File:")
    run_remote("cat /etc/piaware.conf")
    
    # 4. Check Connectivity
    print("\n[4] Checking Network to FlightAware:")
    run_remote("ping -c 2 piaware.flightaware.com")

if __name__ == "__main__":
    main()
