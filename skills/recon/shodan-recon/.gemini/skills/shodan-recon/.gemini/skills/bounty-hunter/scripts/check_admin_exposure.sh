#!/usr/bin/env bash
# Usage: ./check_admin_exposure.sh <url>
URL=$1

echo "[+] Probing $URL for administrative exposure..."

# Check for common sensitive paths
paths=(
  "/admin"
  "/config"
  "/setup"
  "/.env"
  "/.git/config"
  "/robots.txt"
  "/phpinfo.php"
  "/actuator/env"
  "/api/users"
)

for p in "${paths[@]}"; do
  status=$(curl -s -k -o /dev/null -w "%{http_code}" "$URL$p")
  if [[ "$status" == "200" ]]; then
    echo "[!] FOUND: $URL$p (Status: 200)"
    # Quick content check for sensitive strings
    curl -s -k "$URL$p" | grep -iE "password|secret|key|db_user|token|access_token" | head -n 5
  fi
done
