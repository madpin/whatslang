#!/bin/bash

# Script to update docker-compose.registry.yml with actual repository information
# Usage: ./scripts/update-registry-config.sh <owner>/<repo>
# Example: ./scripts/update-registry-config.sh madpin/whatslang

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if repository path is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Repository path not provided${NC}"
    echo "Usage: $0 <owner>/<repo>"
    echo "Example: $0 madpin/whatslang"
    exit 1
fi

REPO_PATH="$1"
REGISTRY_FILE="docker-compose.registry.yml"

# Check if file exists
if [ ! -f "$REGISTRY_FILE" ]; then
    echo -e "${RED}Error: $REGISTRY_FILE not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Updating $REGISTRY_FILE with repository: $REPO_PATH${NC}"

# Create backup
cp "$REGISTRY_FILE" "${REGISTRY_FILE}.bak"
echo -e "${GREEN}Created backup: ${REGISTRY_FILE}.bak${NC}"

# Update the file
sed -i.tmp "s|ghcr.io/<owner>/<repo>/|ghcr.io/${REPO_PATH}/|g" "$REGISTRY_FILE"
rm "${REGISTRY_FILE}.tmp"

echo -e "${GREEN}Successfully updated $REGISTRY_FILE${NC}"
echo ""
echo "Backend image: ghcr.io/${REPO_PATH}/backend:latest"
echo "Frontend image: ghcr.io/${REPO_PATH}/frontend:latest"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Authenticate with GitHub Container Registry:"
echo "   echo \$GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin"
echo ""
echo "2. Pull and run the images:"
echo "   docker-compose -f docker-compose.registry.yml up -d"

