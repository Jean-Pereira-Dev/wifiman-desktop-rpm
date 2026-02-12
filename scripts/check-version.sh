#!/bin/bash
# Script to check for new wifiman-desktop versions

set -e

WIFIMAN_URL="https://desktop.wifiman.com"
SPEC_FILE="${SPEC_FILE:-wifiman-desktop.spec}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Checking for new wifiman-desktop versions..."
echo

# Get current version from spec file
if [ ! -f "$SPEC_FILE" ]; then
    echo -e "${RED}Error: Spec file not found: $SPEC_FILE${NC}"
    exit 1
fi

CURRENT_VERSION=$(grep "^Version:" "$SPEC_FILE" | awk '{print $2}')
echo -e "Current version in spec: ${GREEN}${CURRENT_VERSION}${NC}"

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Function to check if a version exists
check_version() {
    local version=$1
    # Try new format first (1.x.x uses this)
    local url="${WIFIMAN_URL}/wifiman-desktop-${version}-amd64.deb"
    
    if curl -I --silent --fail --max-time 3 "$url" >/dev/null 2>&1; then
        return 0
    fi
    
    # Try old format (0.x.x uses this)
    url="${WIFIMAN_URL}/wifiman-desktop-${version}-linux-amd64.deb"
    if curl -I --silent --fail --max-time 3 "$url" >/dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

echo
echo "Fetching latest version from manifest..."

# Get latest version from the official manifest file
MANIFEST_URL="https://desktop.wifiman.com/wifiman-desktop-linux-manifest.json"
LATEST_VERSION=$(curl -s "$MANIFEST_URL" | grep -oP '"version"\s*:\s*"\K[^"]+' | head -1)

if [ -z "$LATEST_VERSION" ]; then
    echo -e "${YELLOW}Warning: Could not fetch latest version from manifest${NC}"
    LATEST_VERSION="unknown"
else
    echo -e "Latest version from manifest: ${GREEN}${LATEST_VERSION}${NC}"
fi

echo
echo "Checking if current version is still available..."
if check_version "$CURRENT_VERSION"; then
    echo -e "${GREEN}✓${NC} Version $CURRENT_VERSION is available"
else
    echo -e "${RED}✗${NC} Version $CURRENT_VERSION is NOT available"
    echo -e "${YELLOW}Warning: Current version may have been removed or URL changed${NC}"
fi

if [ "$LATEST_VERSION" != "unknown" ]; then
    echo
    echo "Checking if latest version is available..."
    if check_version "$LATEST_VERSION"; then
        echo -e "${GREEN}✓${NC} Version $LATEST_VERSION is available"
    else
        echo -e "${YELLOW}Warning: Latest version may not be accessible yet${NC}"
    fi
fi

echo
echo "================================"
if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
    echo -e "${GREEN}You are up to date!${NC}"
    echo "Current version: $CURRENT_VERSION"
else
    echo -e "${YELLOW}New version available!${NC}"
    echo "Current version: $CURRENT_VERSION"
    echo -e "Latest version:  ${GREEN}${LATEST_VERSION}${NC}"
    echo
    echo "To update, run:"
    echo "  sed -i 's/^Version:.*/Version:  $LATEST_VERSION/' $SPEC_FILE"
fi
echo "================================"

# Exit with code 10 if update is available (useful for automation)
if [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
    exit 10
fi
