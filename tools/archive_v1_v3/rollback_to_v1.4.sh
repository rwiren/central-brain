#!/bin/bash
# ==============================================================================
# Script Name: rollback_to_v1.4.sh
# Description: Force-reverts the fleet to git tag v1.4 (Known Good State).
#              Uses 'git push -f' to overwrite the current broken master on remote.
# Execution:   Run on Local Machine (MacBook)
# ==============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[INFO] Initiating Emergency Rollback to Tag: v1.4${NC}"

# 1. Verify we are in a git repo
if [ ! -d ".git" ]; then
    echo -e "${RED}[ERROR] Not a git repository. Navigate to your project folder first.${NC}"
    exit 1
fi

# 2. Fetch all tags to ensure we have v1.4 locally
echo -e "${YELLOW}[STEP 1] Fetching tags...${NC}"
git fetch --tags

# 3. Check if tag exists
if git rev-parse "v1.4" >/dev/null 2>&1; then
    echo -e "${GREEN}[OK] Tag v1.4 found.${NC}"
else
    echo -e "${RED}[CRITICAL] Tag v1.4 does not exist in this repo!${NC}"
    echo -e "Available tags:"
    git tag
    exit 1
fi

# 4. Checkout the specific tag (Detached HEAD state is fine here)
echo -e "${YELLOW}[STEP 2] Checking out v1.4...${NC}"
git checkout v1.4

# 5. Force Push to Balena
# Note: We push the local 'detached head' (v1.4) to the remote 'master' branch
echo -e "${YELLOW}[STEP 3] Pushing v1.4 to Balena Remote... (This triggers the build)${NC}"
# Replace 'balena' with your actual remote name if different (e.g., 'production')
REMOTE_NAME="balena" 

if git push -f $REMOTE_NAME HEAD:master; then
    echo -e "${GREEN}======================================================${NC}"
    echo -e "${GREEN} ROLLBACK DEPLOYED. MONITOR BALENA DASHBOARD.${NC}"
    echo -e "${GREEN}======================================================${NC}"
    
    # 6. Return local git to main/master so you aren't stuck in detached head
    echo -e "${YELLOW}[INFO] Returning local repo to main branch...${NC}"
    git checkout main 2>/dev/null || git checkout master
else
    echo -e "${RED}[FAIL] Git push failed. Check your remote connection.${NC}"
fi
