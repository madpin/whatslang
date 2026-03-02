#!/bin/bash
# Deployment Verification Script
# Run this script to verify all changes are working correctly

set -e

echo "=========================================="
echo "WhatsLang Deployment Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if files exist
echo "1. Checking file integrity..."
if [ -f "frontend/app.js" ]; then
    print_success "app.js exists"
else
    print_error "app.js missing"
    exit 1
fi

if [ -f "frontend/index.html" ]; then
    print_success "index.html exists"
else
    print_error "index.html missing"
    exit 1
fi

if [ -f "api/main.py" ]; then
    print_success "main.py exists"
else
    print_error "main.py missing"
    exit 1
fi

# Check for cache-busting version parameter
echo ""
echo "2. Checking cache-busting..."
if grep -q "app.js?v=" "frontend/index.html"; then
    VERSION=$(grep -o "app.js?v=[^\"]*" "frontend/index.html" | cut -d'=' -f2)
    print_success "Cache-busting version: $VERSION"
else
    print_error "No cache-busting version found"
    exit 1
fi

# Check for defensive checks in app.js
echo ""
echo "3. Checking data validation fixes..."

if grep -q "if (!Array.isArray(state.chats))" "frontend/app.js"; then
    print_success "state.chats validation in updateDashboardStats"
else
    print_error "Missing state.chats validation"
    exit 1
fi

if grep -q "if (!Array.isArray(chats))" "frontend/app.js"; then
    print_success "chats validation in displayChats"
else
    print_error "Missing chats validation in displayChats"
    exit 1
fi

if grep -q "Array.isArray(data.chats) ? data.chats : \[\]" "frontend/app.js"; then
    print_success "API response validation in loadChats"
else
    print_error "Missing API response validation"
    exit 1
fi

# Check for cache control headers
echo ""
echo "4. Checking cache control headers..."
if grep -q "Cache-Control" "api/main.py"; then
    print_success "Cache control headers present"
else
    print_error "Missing cache control headers"
    exit 1
fi

# Check for favicon endpoint
echo ""
echo "5. Checking favicon endpoint..."
if grep -q "@app.get(\"/favicon.ico\")" "api/main.py"; then
    print_success "Favicon endpoint present"
else
    print_error "Missing favicon endpoint"
    exit 1
fi

# Count defensive checks
echo ""
echo "6. Counting defensive checks..."
COUNT=$(grep -c "if (!Array.isArray(" "frontend/app.js" || true)
print_success "Found $COUNT Array.isArray() checks"

# Check git status
echo ""
echo "7. Checking git status..."
if [ -d ".git" ]; then
    if git diff --quiet; then
        print_warning "No uncommitted changes"
    else
        print_warning "You have uncommitted changes - remember to commit!"
    fi
else
    print_warning "Not a git repository"
fi

# Summary
echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Commit changes: git add . && git commit -m 'Fix cache and validation'"
echo "2. Push to remote: git push origin v2"
echo "3. Wait for deployment"
echo "4. Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)"
echo "5. Check console for errors"
echo ""
echo "If issues persist:"
echo "- Clear browser cache completely"
echo "- Try incognito/private mode"
echo "- Check deployment logs"
echo ""

exit 0

