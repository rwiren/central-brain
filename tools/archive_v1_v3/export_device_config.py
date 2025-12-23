#!/usr/bin/env python3
"""
Script: export_device_config.py
Version: 1.0.0
Description: 
    Exports all Device Variables for a specific Balena UUID to a JSON file.
    Useful for backups or verifying configuration.
    
    Usage:
    python3 tools/export_device_config.py --uuid <DEVICE_UUID> [--output config.json]
"""

import subprocess
import json
import argparse
import sys
import os
from datetime import datetime

def run_command(cmd_list):
    """Runs a command safely without shell expansion."""
    try:
        result = subprocess.run(cmd_list, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {' '.join(cmd_list)}")
        print(f"   Error: {e.stderr.strip()}")
        return None

def get_variables(uuid):
    """Fetches variables using balena-cli."""
    print(f"🔍 Fetching variables for device: {uuid}...")
    
    # CLI v23+ command
    cmd = ["balena", "env", "list", "--device", uuid, "--json"]
    output = run_command(cmd)
    
    if not output:
        return []
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON response from Balena CLI.")
        return []

def main():
    parser = argparse.ArgumentParser(description="Export Balena Device Config")
    parser.add_argument("--uuid", required=True, help="UUID of the device to export")
    parser.add_argument("--output", default=None, help="Output JSON file (default: <uuid>_config.json)")
    
    args = parser.parse_args()

    # 1. Check CLI
    version = run_command(["balena", "version"])
    if not version:
        print("❌ Balena CLI not found. Please install it.")
        sys.exit(1)
    
    # 2. Fetch
    vars_list = get_variables(args.uuid)
    if not vars_list:
        print("⚠️  No variables found (or device not accessible).")
        sys.exit(1)

    # 3. Process & Filter
    # We create a clean dictionary: { "VARIABLE_NAME": "VALUE" }
    clean_config = {}
    system_vars = {}
    
    IGNORED_PREFIXES = ["BALENA_", "RESIN_", "OS_"]

    for item in vars_list:
        key = item.get('name')
        value = item.get('value')
        
        if any(key.startswith(prefix) for prefix in IGNORED_PREFIXES):
            system_vars[key] = value
        else:
            clean_config[key] = value

    # 4. Display
    print(f"\n📋 FOUND {len(clean_config)} USER VARIABLES:")
    print("-" * 60)
    print(f"{'KEY':<30} | {'VALUE':<25}")
    print("-" * 60)
    for k, v in sorted(clean_config.items()):
        # Truncate for display
        disp_v = (v[:22] + '..') if len(v) > 22 else v
        print(f"{k:<30} | {disp_v:<25}")
    print("-" * 60)
    print(f"   (Plus {len(system_vars)} system variables)")

    # 5. Save to File
    filename = args.output if args.output else f"{args.uuid}_config.json"
    
    export_data = {
        "device_uuid": args.uuid,
        "exported_at": datetime.now().isoformat(),
        "user_variables": clean_config,
        "system_variables": system_vars
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=4)
        print(f"\n✅ Configuration saved to: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"\n❌ Failed to save file: {e}")

if __name__ == "__main__":
    main()
