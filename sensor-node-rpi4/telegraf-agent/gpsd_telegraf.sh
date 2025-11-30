#!/bin/bash
# file: gpsd_telegraf.sh

# Unique Temp File
TMP_FILE="/tmp/gps_data_${$}.json"

# Capture 5s of data
timeout 5s gpspipe -w -n 30 > "$TMP_FILE" 2>/dev/null

# Extract unique lines
TPV=$(grep '"class":"TPV"' "$TMP_FILE" | tail -n 1)
SKY=$(grep '"class":"SKY"' "$TMP_FILE" | tail -n 1)

# Output as a JSON Array to satisfy Telegraf
if [ -n "$TPV" ] && [ -n "$SKY" ]; then
  echo "[$TPV, $SKY]"
elif [ -n "$TPV" ]; then
  echo "[$TPV]"
elif [ -n "$SKY" ]; then
  echo "[$SKY]"
fi

# Cleanup
rm -f "$TMP_FILE"
