#!/bin/bash
# ==============================================================================
# Script: run.sh
# Service: ADSB-Feeders Process Manager (Fault Tolerant)
# Version: 4.0.0 (Level 4 AI Support)
# ==============================================================================

echo "[INIT] Starting ADSB Feeder Stack (v4.0.0 Level 4)..."

# Function to run scripts in the background with auto-restart
run_script() {
    echo "   -> Launching $1..."
    while true; do
        python3 -u "$1"
        echo "   ⚠️  $1 crashed! Restarting in 15s..."
        sleep 15
    done &
}

# --- 1. CORE TELEMETRY ---
# High-speed local position updates (10Hz potential)
run_script "readsb_position_feeder.py"
# Local station statistics (Aircraft counts, range)
run_script "readsb_feeder.py"

# --- 2. EXTERNAL INTELLIGENCE ---
# Verified Global Truth data
run_script "opensky_feeder.py"
# Real-time Aviation Weather (EFHK)
run_script "metar_feeder.py"

# --- 3. AI & LOGIC ENGINES ---
# Gamification engine (RF Battles)
run_script "battle_engine.py"
# Live AI Training Labeler (The "Teacher")
run_script "live_labeler.py"

# Keep container alive
tail -f /dev/null
