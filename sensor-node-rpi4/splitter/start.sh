#!/bin/bash

# List of Mountpoints to try (in order of preference)
# 1. Primary: Lintuvaara (10km)
# 2. Backup 1: teira (Espoo)
# 3. Backup 2: knummi_kha (Kirkkonummi)
# 4. Backup 3: DGNSS (National Backup)

MOUNTS=("Lintuvaara" "teira" "knummi_kha" "DGNSS")

while true; do
    for MOUNT in "${MOUNTS[@]}"; do
        echo "[SPLITTER] Trying to connect to Mountpoint: $MOUNT"
        
        # Run str2str
        # If it connects, this command stays running forever.
        # If it fails or disconnects, the loop continues to the next mountpoint.
        str2str -in serial://ttyACM0:115200:8:n:1#ntrip://${NTRIP_USER}:${NTRIP_PASS}@${NTRIP_HOST}:${NTRIP_PORT}/${MOUNT} -out tcpsvr://:2000
        
        echo "[SPLITTER] Connection to $MOUNT lost or failed. Switching to next backup..."
        sleep 5 # Wait 5 seconds before retry
    done
    echo "[SPLITTER] All mountpoints failed. Restarting loop..."
done
