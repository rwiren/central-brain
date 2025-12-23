#!/bin/bash
# ==============================================================================
# Script Name: preserve_tools_snapshot.sh
# Description: Creates a compressed archive of the current 'tools' directory
#              and saves it to the Desktop to prevent data loss during Git Rollback.
# Context:     Pre-Rollback Safety Measure.
# ==============================================================================

# 1. Configuration
# ----------------
SOURCE_DIR=$(pwd)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="isac_tools_snapshot_${TIMESTAMP}.tar.gz"
DESTINATION="$HOME/Desktop/${BACKUP_NAME}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${YELLOW}[INFO] Initiating Safety Snapshot for: ${SOURCE_DIR}${NC}"

# 2. Verify we are in the correct directory
# -----------------------------------------
if [ ! -f "live_rf_battle_v6.1.py" ]; then
    echo -e "${YELLOW}[WARN] Are you in the 'tools' folder? 'live_rf_battle_v6.1.py' not found.${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 3. Create Archive
# -----------------
echo -e "${CYAN}[STEP 1] Archiving contents to Desktop...${NC}"
tar --exclude='.git' -czf "$DESTINATION" .

# 4. Verify Archive
# -----------------
if [ -f "$DESTINATION" ]; then
    FILE_SIZE=$(du -h "$DESTINATION" | cut -f1)
    echo -e "${GREEN}[SUCCESS] Backup secured at: ${DESTINATION}${NC}"
    echo -e "${GREEN}[STATS] Archive Size: ${FILE_SIZE}${NC}"
    
    echo -e "${YELLOW}[INFO] The following Critical Version 6+ files are secured:${NC}"
    tar -tf "$DESTINATION" | grep "v6"
else
    echo -e "${RED}[FAIL] Archive creation failed.${NC}"
    exit 1
fi

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN} READY FOR ROLLBACK. YOUR TOOLS ARE SAFE.${NC}"
echo -e "${GREEN}======================================================${NC}"
