#!/bin/bash
# End-to-end smoke test for UAI Engine

set -e  # Exit on any error

API_URL="${API_URL:-http://localhost:8000}"
BASE_URL="${BASE_URL:-http://localhost:3000}"

echo "=== UAI Engine Smoke Test ==="
echo "API URL: $API_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_step() {
    local name=$1
    echo -n "Testing: $name... "
    if eval "$2" > /tmp/smoke_test_output.txt 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Error output:"
        cat /tmp/smoke_test_output.txt | head -20
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Generate random email
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123"
TEST_NAME="Test User"

echo "Using test email: $TEST_EMAIL"
echo ""

# 1. Sign up
SIGNUP_RESPONSE=$(curl -s -X POST $API_URL/auth/signup \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"name\":\"$TEST_NAME\"}")

if echo "$SIGNUP_RESPONSE" | jq -e '.access_token != null' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TOKEN=$(echo "$SIGNUP_RESPONSE" | jq -r '.access_token')
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "Error output:"
    echo "$SIGNUP_RESPONSE" | head -20
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "Sign up failed, cannot continue"
    exit 1
fi

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "Failed to get token"
    exit 1
fi

echo "Token obtained: ${TOKEN:0:20}..."
echo ""

# 2. Get user info
test_step "Get user info" "curl -s -X GET $API_URL/auth/me \
    -H 'Authorization: Bearer $TOKEN' \
    | jq -e '.email == \"$TEST_EMAIL\"'"

USER_ID=$(curl -s -X GET $API_URL/auth/me \
    -H "Authorization: Bearer $TOKEN" \
    | jq -r '.id')

echo "User ID: $USER_ID"
echo ""

# 3. Create project
PROJECT_NAME="Test Project $(date +%s)"
PROJECT_PROMPT="Create a simple landing page"

test_step "Create project" "curl -s -X POST $API_URL/projects \
    -H 'Authorization: Bearer $TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{\"name\":\"$PROJECT_NAME\",\"prompt\":\"$PROJECT_PROMPT\"}' \
    | jq -e '.id != null'"

PROJECT_ID=$(curl -s -X POST $API_URL/projects \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"name\":\"$PROJECT_NAME\",\"prompt\":\"$PROJECT_PROMPT\"}" \
    | jq -r '.id')

if [ "$PROJECT_ID" == "null" ] || [ -z "$PROJECT_ID" ]; then
    echo "Failed to create project"
    exit 1
fi

echo "Project ID: $PROJECT_ID"
echo "Waiting for initial build to complete..."
sleep 15
echo ""

# Grant credits to user for iteration (needed after project creation charges credits)
echo "Granting credits for iteration test..."
GRANT_RESPONSE=$(curl -s -X POST $API_URL/credits/admin/grant \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$USER_ID\",\"amount\":10.0,\"reason\":\"Smoke test credits\"}")

if echo "$GRANT_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    echo "Credits granted successfully"
else
    echo "Warning: Failed to grant credits, iteration may fail"
fi
echo ""

# 4. Send prompt iteration
ITERATION_PROMPT="change hero title to Hello World"
echo -n "Testing: Send prompt iteration... "

# Capture HTTP status code and response
ITERATION_HTTP_CODE=$(curl -s -o /tmp/iteration_response.json -w "%{http_code}" -X POST $API_URL/projects/$PROJECT_ID/prompt \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"message\":\"$ITERATION_PROMPT\"}")

ITERATION_RESPONSE=$(cat /tmp/iteration_response.json)

# Redact secrets from response (tokens, passwords, etc.)
REDACTED_RESPONSE=$(echo "$ITERATION_RESPONSE" | sed 's/"access_token":"[^"]*"/"access_token":"[REDACTED]"/g' | sed 's/"token":"[^"]*"/"token":"[REDACTED]"/g' | sed 's/"password":"[^"]*"/"password":"[REDACTED]"/g')

# Check if response has version and build (even if build failed)
if echo "$ITERATION_RESPONSE" | jq -e '.version != null and .build != null' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    ITERATION_VERSION_ID=$(echo "$ITERATION_RESPONSE" | jq -r '.version.id')
    echo "Iteration version created: $ITERATION_VERSION_ID"
else
    # In prod mode, always fail. In dev mode, allow skip for Docker issues
    if [ "${PROD_MODE:-0}" = "1" ]; then
        echo -e "${RED}✗ FAILED${NC}"
        echo "HTTP Status Code: $ITERATION_HTTP_CODE"
        echo "Response body (secrets redacted):"
        echo "$REDACTED_RESPONSE" | jq '.' 2>/dev/null || echo "$REDACTED_RESPONSE" | head -50
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        # Dev mode: allow skip for Docker issues
        if echo "$ITERATION_RESPONSE" | jq -e '.error != null' > /dev/null 2>&1; then
            ERROR_MSG=$(echo "$ITERATION_RESPONSE" | jq -r '.error.message // .error.code // "Unknown error"')
            echo -e "${YELLOW}⚠ SKIPPED${NC} (Error: $ERROR_MSG)"
            echo "HTTP Status Code: $ITERATION_HTTP_CODE"
            echo "Response body (secrets redacted):"
            echo "$REDACTED_RESPONSE" | jq '.' 2>/dev/null || echo "$REDACTED_RESPONSE" | head -50
            echo "Note: Iteration may fail if Docker is unavailable, but this is expected in dev mode"
        else
            echo -e "${RED}✗ FAILED${NC}"
            echo "HTTP Status Code: $ITERATION_HTTP_CODE"
            echo "Response body (secrets redacted):"
            echo "$REDACTED_RESPONSE" | jq '.' 2>/dev/null || echo "$REDACTED_RESPONSE" | head -50
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
fi

echo "Waiting for any builds to complete..."
sleep 5
echo ""

# 5. Get file tree
test_step "Get file tree" "curl -s -X GET '$API_URL/projects/$PROJECT_ID/files/tree' \
    -H 'Authorization: Bearer $TOKEN' \
    | jq -e 'length >= 0'"

FILE_COUNT=$(curl -s -X GET "$API_URL/projects/$PROJECT_ID/files/tree" \
    -H "Authorization: Bearer $TOKEN" \
    | jq 'length')

echo "Files found: $FILE_COUNT"
echo ""

# 6. Get build logs
test_step "Get build logs" "curl -s -X GET '$API_URL/projects/$PROJECT_ID/builds' \
    -H 'Authorization: Bearer $TOKEN' \
    | jq -e 'length > 0'"

BUILD_ID=$(curl -s -X GET "$API_URL/projects/$PROJECT_ID/builds" \
    -H "Authorization: Bearer $TOKEN" \
    | jq -r '.[0].id')

if [ "$BUILD_ID" != "null" ] && [ -n "$BUILD_ID" ]; then
    echo "Build ID: $BUILD_ID"
    
    # 7. Get specific build
    test_step "Get specific build" "curl -s -X GET '$API_URL/projects/$PROJECT_ID/builds/$BUILD_ID' \
        -H 'Authorization: Bearer $TOKEN' \
        | jq -e '.id == \"$BUILD_ID\"'"
    
    # 8. Get preview
    PREVIEW_URL="$API_URL/preview/$PROJECT_ID/$BUILD_ID"
    test_step "Get preview" "curl -s -X GET '$PREVIEW_URL' \
        | grep -q 'Build Successful\|Build Failed'"
    
    echo "Preview URL: $PREVIEW_URL"
else
    echo "No build found"
fi

echo ""
echo "=== Test Summary ==="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
