#!/bin/bash
# ==============================================================================
# Script Name: rollback_to_v1.4.0_fix.sh
# Version: 1.1 (Tag Fix)
# Description: Force-reverts the fleet to git tag v1.4.0.
#              Includes remote detection to find the correct Balena endpoint.
# ==============================================================================

# Configuration
TARGET_TAG="v1.4.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[INFO] Initiating Emergency Rollback to Tag: ${TARGET_TAG}${NC}"

# 1. Verify Git Repo
if [ ! -d ".git" ]; then
    echo -e "${RED}[ERROR] Run this from the root of your git repository.${NC}"
    exit 1
fi

# 2. Fetch Tags
echo -e "${YELLOW}[STEP 1] Fetching tags...${NC}"
git fetch --tags

# 3. Verify Tag Exists
if git rev-parse "$TARGET_TAG" >/dev/null 2>&1; then
    echo -e "${GREEN}[OK] Tag ${TARGET_TAG} found.${NC}"
else
    echo -e "${RED}[CRITICAL] Tag ${TARGET_TAG} NOT found!${NC}"
    echo -e "Available tags:"
    git tag
    exit 1
fi

# 4. Detect Balena Remote
# We need to push to the Balena builder, not just GitHub (origin)
REMOTE_NAME=""
if git remote | grep -q "balena"; then
    REMOTE_NAME="balena"
elif git remote | grep -q "production"; then
    REMOTE_NAME="production"
else
    echo -e "${RED}[ERROR] No 'balena' remote found.${NC}"
    echo -e "${YELLOW}Please type the name of your Balena remote from the list below:${NC}"
    git remote -v
    read -p "Remote Name: " REMOTE_NAME
fi

echo -e "${GREEN}[INFO] Target Remote: ${REMOTE_NAME}${NC}"

# 5. Checkout Tag
echo -e "${YELLOW}[STEP 2] Checking out ${TARGET_TAG}...${NC}"
git checkout "$TARGET_TAG"

# 6. Force Push Deployment
echo -e "${YELLOW}[STEP 3] Pushing ${TARGET_TAG} to ${REMOTE_NAME} master...${NC}"
echo -e "${YELLOW}       (This triggers the build on Balena Cloud)${NC}"

if git push -f "$REMOTE_NAME" HEAD:master; then
    echo -e "${GREEN}======================================================${NC}"
    echo -e "${GREEN} SUCCESS: Rollback triggered for ${TARGET_TAG}.${NC}"
    echo -e "${GREEN} Monitor the Balena Dashboard for the 'Updating' status.${NC}"
    echo -e "${GREEN}======================================================${NC}"
    
    # 7. Safety Return
    echo -e "${YELLOW}[INFO] Returning local repo to main branch...${NC}"
    git checkout main 2>/dev/null || git checkout master
else
    echo -e "${RED}[FAIL] Push failed. Check your internet or remote permissions.${NC}"
fi
