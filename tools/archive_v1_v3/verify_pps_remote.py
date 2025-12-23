#!/usr/bin/env python3
# ==============================================================================
# Script Name: verify_pps_remote.py
# Version: 2.1.0 (Remote Edition)
# Date: 2025-12-04
# Author: System Architect
# Description: Connects to a remote sensor node via SSH to validate:
#              1. Hardware Layer: /sys/class/pps/pps0/assert (Kernel interrupts)
#              2. Software Layer: chronyc sources (Time synchronization lock)
# Usage:       python3 verify_pps_remote.py <target_ip> <ssh_port>
# ==============================================================================

import subprocess
import sys
import time
import re

# --- Configuration ---
DEFAULT_TARGET_IP = "192.168.1.153" # keimola-office (WiFi)
DEFAULT_SSH_PORT = "22222"          # Balena standard port
SSH_USER = "root"

def run_ssh_command(ip, port, command):
    """Executes a command on the remote node and returns the output."""
    ssh_cmd = [
        "ssh",
        "-p", port,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=5",
        f"{SSH_USER}@{ip}",
        command
    ]
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ SSH Execution Error: {e.stderr.strip()}")
        return None
    except Exception as e:
        print(f"❌ General Error: {e}")
        return None

def check_hardware_pps(ip, port):
    """Checks if the PPS wire is generating interrupts on the remote device."""
    print(f"\n--- 1. HARDWARE LAYER (Physical Wire Check) ---")
    
    cmd_read = "cat /sys/class/pps/pps0/assert 2>/dev/null"
    
    # Read 1
    start_val = run_ssh_command(ip, port, cmd_read)
    if not start_val:
        print("❌ ERROR: Could not read /sys/class/pps/pps0/assert. Is overlay loaded?")
        return False
        
    # Parse the count (Format: '123456.789#count')
    try:
        start_count = int(start_val.split('#')[1])
    except IndexError:
        print(f"❌ ERROR: Unexpected format: {start_val}")
        return False

    print(f"   Initial Pulse Count: {start_count}")
    print("   Waiting 2 seconds to detect heartbeat...")
    time.sleep(2)
    
    # Read 2
    end_val = run_ssh_command(ip, port, cmd_read)
    if not end_val: return False
    end_count = int(end_val.split('#')[1])
    
    delta = end_count - start_count
    
    if delta >= 2:
        print(f"✅ SUCCESS: Detected {delta} new pulses. Wire is active.")
        return True
    else:
        print(f"❌ FAILURE: Count did not increase. Wire is connected but silent.")
        return False

def check_software_lock(ip, port):
    """Checks if Chrony is actively disciplined by the PPS source."""
    print(f"\n--- 2. SOFTWARE LAYER (Chrony Synchronization) ---")
    
    cmd_chrony = "chronyc sources -v"
    output = run_ssh_command(ip, port, cmd_chrony)
    
    if not output:
        print("❌ ERROR: Could not run 'chronyc'. Is Chrony installed?")
        return

    # Look for the PPS line status char (#*, #+, #?)
    # Regex captures the status char at start of line before 'PPS'
    match = re.search(r"^([#\^][\*\+\?x-])\s+PPS", output, re.MULTILINE)
    
    if match:
        status = match.group(1)
        
        # Extract offset data for context
        pps_line = [line for line in output.split('\n') if "PPS" in line][0]
        
        if "#*" in status:
            print(f"🏆 SYSTEM LOCKED: Chrony is fully synced to PPS.")
            print(f"   Raw Status: {pps_line}")
        elif "#+" in status:
            print(f"✅ GOOD: PPS is a candidate source (Standby).")
            print(f"   Raw Status: {pps_line}")
        elif "#?" in status:
            print(f"⚠️  WARNING: PPS is unreachable/untrusted (Ghost Pulse).")
            print(f"   Raw Status: {pps_line}")
        else:
            print(f"❌ ERROR: PPS status unknown ({status}).")
            print(f"   Raw Status: {pps_line}")
    else:
        print("❌ FAILURE: No PPS source found in Chrony configuration.")

def main():
    # Parse Args
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET_IP
    port = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SSH_PORT

    print("=======================================")
    print("   REMOTE PPS VERIFICATION TOOL        ")
    print(f"   Target: {target}:{port}")
    print("=======================================")

    hw_ok = check_hardware_pps(target, port)
    if hw_ok:
        check_software_lock(target, port)
    else:
        print("\n⛔ ABORTING: Cannot verify software lock if hardware is silent.")

if __name__ == "__main__":
    main()
