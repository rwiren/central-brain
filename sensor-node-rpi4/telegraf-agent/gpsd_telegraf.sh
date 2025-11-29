#!/bin/bash
# file: gpsd_telegraf.sh

# Generate a unique temp file using the Process ID ($$)
# This prevents file permission conflicts between 'root' and 'telegraf' user
TMP_FILE="/tmp/gps_data_${$}.json"

# 1. Capture 5 seconds of raw data to ensure we catch the 'SKY' message
# -w: JSON output
# -n 30: Limit to 30 messages max
# timeout 5s: Hard stop to prevent hanging
timeout 5s gpspipe -w -n 30 > "$TMP_FILE" 2>/dev/null

# 2. Check if file exists (in case gpspipe failed entirely)
if [ -s "$TMP_FILE" ]; then
    # Extract the latest Position (TPV)
    grep '"class":"TPV"' "$TMP_FILE" | tail -n 1

    # Extract the latest Satellite Info (SKY)
    grep '"class":"SKY"' "$TMP_FILE" | tail -n 1
fi

# 3. Cleanup immediately
rm -f "$TMP_FILE"

