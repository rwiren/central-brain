#!/bin/bash
# ==============================================================================
# Script Name: emergency_restore_services.sh
# Version: 1.0 (Recovery Release)
# Date: 2025-12-04
# Author: System Architect (AI Assistant)
# Description: Priority 1 script to restart InfluxDB/Grafana and verify ports
#              to fix "Connection Refused" errors.
# ==============================================================================

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[INFO] Starting Emergency System Restore...${NC}"

# ------------------------------------------------------------------------------
# 1. STOP SERVICES (To ensure clean state)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 1] Stopping existing services to clear locks...${NC}"
sudo systemctl stop influxdb
sudo systemctl stop grafana-server
sleep 2

# ------------------------------------------------------------------------------
# 2. START INFLUXDB ( The Critical Failure Point)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 2] Starting InfluxDB...${NC}"
sudo systemctl unmask influxdb 2>/dev/null # Ensure it's not masked
sudo systemctl start influxdb

# Wait for InfluxDB to initialize
echo -e "${YELLOW}[WAIT] Waiting 10 seconds for InfluxDB to bind to port 8086...${NC}"
sleep 10

# Check InfluxDB Status
if systemctl is-active --quiet influxdb; then
    echo -e "${GREEN}[OK] InfluxDB service is RUNNING.${NC}"
else
    echo -e "${RED}[CRITICAL] InfluxDB failed to start. Check 'journalctl -u influxdb -e'${NC}"
fi

# ------------------------------------------------------------------------------
# 3. VERIFY PORT 8086 (Connection Refused Fix)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 3] Verifying Port 8086 (InfluxDB)...${NC}"
if ss -tuln | grep -q ":8086"; then
    echo -e "${GREEN}[OK] Port 8086 is LISTENING (Connection Refused should be gone).${NC}"
else
    echo -e "${RED}[CRITICAL] Port 8086 is NOT listening. InfluxDB config error or crash.${NC}"
fi

# ------------------------------------------------------------------------------
# 4. START GRAFANA
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 4] Starting Grafana Server...${NC}"
sudo systemctl start grafana-server
sleep 5

if systemctl is-active --quiet grafana-server; then
    echo -e "${GREEN}[OK] Grafana service is RUNNING.${NC}"
else
    echo -e "${RED}[ERROR] Grafana failed to start.${NC}"
fi

# ------------------------------------------------------------------------------
# 5. FIREWALL CHECK (UFW)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 5] Ensuring Localhost traffic is allowed...${NC}"
# Allow traffic from localhost to localhost
sudo ufw allow from 127.0.0.1 to any
sudo ufw allow 8086/tcp
sudo ufw allow 3000/tcp
echo -e "${GREEN}[OK] Firewall rules updated for Ports 3000 and 8086.${NC}"

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN} RESTORE SEQUENCE COMPLETE. PLEASE CHECK DASHBOARD.${NC}"
echo -e "${GREEN}======================================================${NC}"
