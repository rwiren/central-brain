#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: check_influx_health.sh
# Description: Verifies that the Fleet is successfully pushing data to InfluxDB.
# Architect:   Gemini
# Target:      InfluxDB (http://192.168.1.134:8086)
# -----------------------------------------------------------------------------

INFLUX_HOST="192.168.1.134"
INFLUX_PORT="8086"
DB_NAME="readsb"

# Function to run a curl query
query_influx() {
    local query="$1"
    curl -s -G "http://${INFLUX_HOST}:${INFLUX_PORT}/query" \
        --data-urlencode "db=${DB_NAME}" \
        --data-urlencode "q=${query}"
}

echo "--- 📊 INFLUXDB HEALTH CHECK ---"
echo "Target: http://${INFLUX_HOST}:${INFLUX_PORT}"
echo "Database: ${DB_NAME}"
echo "--------------------------------"

# 1. Check Connection
if ! curl -s --head "http://${INFLUX_HOST}:${INFLUX_PORT}/ping" | grep "204 No Content" > /dev/null; then
    echo "❌ [CRITICAL] Cannot connect to InfluxDB at ${INFLUX_HOST}:${INFLUX_PORT}"
    exit 1
else
    echo "✅ [OK] InfluxDB is online and reachable."
fi

# 2. Check Recent System Metrics (CPU)
echo -n "🔍 Checking for recent CPU data (last 5 minutes)... "
# We select the last entry for 'usage_idle' to prove data is flowing
CPU_DATA=$(query_influx "SELECT last(\"usage_idle\") FROM \"cpu\" WHERE time > now() - 5m")

if [[ "$CPU_DATA" == *"usage_idle"* ]]; then
    echo "✅ [SUCCESS]"
    echo "   Data confirms Telegraf is ACTIVE on the fleet."
else
    echo "⚠️ [WARNING]"
    echo "   No CPU data found in the last 5 minutes. Check Balena logs."
fi

# 3. Check for GPS Precision Data (Expected Missing)
echo -n "🔍 Checking for GPS Precision data (satellites)... "
GPS_DATA=$(query_influx "SELECT last(\"satellites_visible\") FROM \"gpsd\" WHERE time > now() - 5m")

if [[ "$GPS_DATA" == *"satellites_visible"* ]]; then
    echo "✅ [FOUND] (Unexpected)"
    echo "   GPS data is present. Did you enable the flag?"
else
    echo "ℹ️ [MISSING] (Expected)"
    echo "   GPS data is absent. This confirms the 'Hotfix' is active and preventing crashes."
fi

echo "--------------------------------"
echo "Done."
