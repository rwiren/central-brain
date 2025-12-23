#!/usr/bin/env python3
"""
Script: clone_device_variables.py
Version: 1.4.0 (Fix: CLI v23 'env set' compatibility)
Description: 
    Migrates Device Variables from a dead device to a new one.
    - Uses 'balena env set' (New CLI syntax).
    - Lists all variables found before copying.
    - Handles quoting safely.
"""

import subprocess
import json
import argparse
import sys
import time

def run_command(cmd_list):
    """Runs a command safely without shell expansion."""
    try:
        # shell=False ensures arguments are passed exactly as is
        result = subprocess.run(cmd_list, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        cmd_str = " ".join(cmd_list)
        print(f"❌ Error running command: {cmd_str}")
        print(f"   Error: {e.stderr.strip()}")
        return None

def get_variables(uuid):
    """Fetches variables from a device using 'env list'."""
    print(f"🔍 Fetching variables from source: {uuid}...")
    
    # CLI v23+ uses 'balena env list'
    cmd = ["balena", "env", "list", "--device", uuid, "--json"]
    output = run_command(cmd)
    
    if not output:
        return []
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON response.")
        return []

def set_variable(uuid, key, value):
    """Sets a variable using 'env set'."""
    print(f"   -> Setting {key}...")
    
    # CLI v23+ uses 'balena env set NAME VALUE --device UUID'
    cmd = ["balena", "env", "set", key, str(value), "--device", uuid]
    run_command(cmd)

def main():
    parser = argparse.ArgumentParser(description="Clone Balena Device Variables")
    parser.add_argument("--source", required=True, help="UUID of the old/dead device")
    parser.add_argument("--target", required=True, help="UUID of the new/fresh device")
    
    args = parser.parse_args()

    # 1. Check CLI Version
    version = run_command(["balena", "version"])
    if not version:
        print("❌ Balena CLI not found.")
        sys.exit(1)
    print(f"✅ Balena CLI: {version}")

    # 2. Fetch Variables
    vars_list = get_variables(args.source)
    if not vars_list:
        print("⚠️  No variables found on source device.")
        sys.exit(1)

    # 3. Filter & List
    IGNORED_PREFIXES = ["BALENA_", "RESIN_", "OS_", "UUID"]
    to_copy = []
    
    print(f"\n📋 FOUND {len(vars_list)} VARIABLES:")
    print("-" * 60)
    print(f"{'KEY':<30} | {'VALUE (Preview)':<25}")
    print("-" * 60)

    for item in vars_list:
        key = item.get('name')
        value = item.get('value')
        
        if any(key.startswith(prefix) for prefix in IGNORED_PREFIXES):
            continue
            
        to_copy.append((key, value))
        # Truncate long values for display
        display_val = (value[:22] + '..') if len(value) > 22 else value
        print(f"{key:<30} | {display_val:<25}")

    print("-" * 60)
    print(f"✅ Ready to clone {len(to_copy)} variables to target: {args.target}")
    confirm = input("   Proceed? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    # 4. Clone
    print("\n🚀 Starting Migration...")
    success = 0
    for key, value in to_copy:
        set_variable(args.target, key, value)
        success += 1
        time.sleep(1) # Rate limit protection

    print(f"\n✅ Done. Transferred {success} variables.")
    print("   Please restart the target device via Dashboard.")

if __name__ == "__main__":
    main()
