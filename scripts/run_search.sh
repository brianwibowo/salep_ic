#!/bin/bash
# Manual or external-cron trigger. Disable the internal scheduler when using cron.
set -euo pipefail
API_URL="${SALEP_API_URL:-http://127.0.0.1:8000}"
COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT
curl --fail --silent --show-error -c "$COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"role":"marketing"}' "$API_URL/api/v1/auth/login" >/dev/null
curl --fail --silent --show-error -b "$COOKIE_JAR" \
  -X POST "$API_URL/api/v1/scheduler/trigger"
curl --fail --silent --show-error -b "$COOKIE_JAR" \
  -X POST "$API_URL/api/v1/auth/logout" >/dev/null
