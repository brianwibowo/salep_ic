#!/bin/bash
# SALEP Lead Generation Runner Script
# Can be run manually or triggered via cron

API_URL="${SALEP_API_URL:-https://salep1.duckdns.org}"

# Auto-compute dates (compatible with both GNU date and macOS BSD date)
YESTERDAY=$(date -d "yesterday" '+%Y-%m-%d' 2>/dev/null || date -v-1d '+%Y-%m-%d' 2>/dev/null || date '+%Y-%m-%d')
TODAY=$(date '+%Y-%m-%d')

echo "==> [$(date '+%Y-%m-%d %H:%M:%S')] Triggering SALEP lead generation..."
echo "==> Range: $YESTERDAY to $TODAY"
echo "==> Target: $API_URL/api/v1/search"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": [
      "jasa website",
      "managed service",
      "cloud server",
      "sistem ERP",
      "software house",
      "cari vendor IT",
      "bikin aplikasi mobile",
      "jasa cybersecurity",
      "data analytics dashboard"
    ],
    "start_date": "'"$YESTERDAY"'",
    "end_date": "'"$TODAY"'",
    "sources": ["mock"],
    "limit": 50
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "==> SUCCESS (HTTP $HTTP_CODE)"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
  echo "==> FAILED (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi
