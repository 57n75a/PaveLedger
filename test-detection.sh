#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# FILL IN THESE FOUR VALUES BEFORE RUNNING
# ============================================================

# Your Supabase anon/publishable key. Find it in Vercel:
# Settings -> Environment Variables -> NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVoc3hlcXZydmdvZWNoZmJ2c2RiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAzNTQ2NjIsImV4cCI6MjEwNTkzMDY2Mn0.OcBjB5O0gy4cqkUtpieZUXKfehV8rQvNbTOWEhoWBQY"

# The vehicle account's password (what you set in Supabase Auth)
PASSWORD="Sinisa1!"

# Path to any small JPEG on your computer to use as the test photo
IMAGE_PATH="/home/sinisa/Documents/PaveLedger/pot-hole1.jpg"

# ============================================================
# These shouldn't need editing
# ============================================================
EMAIL="57n75a@gmail.com"
SUPABASE_URL="https://uhsxeqvrvgoechfbvsdb.supabase.co"
API_BASE="https://paveledger.vercel.app"
ROAD="King Street East"
LAT="43.4516"
LNG="-80.4925"

echo "Step 1: Logging in as $EMAIL..."
AUTH_RESPONSE=$(curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $ANON_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

if [ -z "$ACCESS_TOKEN" ]; then
  echo ""
  echo "Login failed. Here's what Supabase said:"
  echo "$AUTH_RESPONSE"
  exit 1
fi

echo "Login succeeded."
echo ""
echo "Step 2: Sending a test detection to $API_BASE/api/detect ..."

CAPTURED_AT=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_BASE/api/detect" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "road=$ROAD" \
  -F "lat=$LAT" \
  -F "lng=$LNG" \
  -F "accuracy=3.5" \
  -F "lane=Lane 1" \
  -F "capturedAt=$CAPTURED_AT" \
  -F "confidence=0.87" \
  -F "file=@$IMAGE_PATH;type=image/jpeg")

echo ""
echo "Server response:"
echo "$RESPONSE"
echo ""
echo "If you see {\"status\":\"submitted\"} above, it worked."
echo "Log into PaveLedger as owner and check the Investigations view for a new ticket on \"$ROAD\"."
