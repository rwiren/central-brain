#!/bin/bash
# ==============================================================================
# Script: run.sh
# Service: ADSB-Feeders Process Manager (Fault Tolerant)
# ==============================================================================

echo "[INIT] Starting ADSB Feeder Stack (v3.2.0)..."

run_script() {
    echo "   -> Launching $1..."
    while true; do
        python3 -u "$1"
        echo "   ⚠️  $1 crashed! Restarting in 15s..."
        sleep 15
    done &
}

# 1. Core Feeders
run_script "readsb_feeder.py"
run_script "readsb_position_feeder.py"
run_script "opensky_feeder.py"
run_script "battle_engine.py"

# 2. Weather Feeder (FORCED)
# Removed the [ -f ] check so it errors loudly if missing
run_script "metar_feeder.py"

# Keep container alive
tail -f /dev/null
