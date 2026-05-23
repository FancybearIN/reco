#!/usr/bin/env bash
set -uo pipefail

INPUT="$1"
OUT="${2:-runs/subdomain_recon_$(date +%Y%m%d_%H%M%S)}"

if [[ ! -f "$INPUT" ]]; then
  echo "Usage: $0 domains.txt runs/<target>/recon/subdomains"
  exit 1
fi

mkdir -p "$OUT"/{raw,resolved,takeover,logs}

RAW="$OUT/all_raw.txt"
UNIQ="$OUT/all_unique.txt"
RESOLVED="$OUT/resolved.txt"
UNRESOLVED="$OUT/unresolved.txt"
CNAME="$OUT/takeover/cnames.txt"
TAKEOVER="$OUT/takeover/candidates.txt"
MISSING="$OUT/missing_tools.txt"
COVERAGE="$OUT/method_coverage.jsonl"

touch "$RAW" "$MISSING" "$COVERAGE"

log_method() {
  echo "{\"method\":\"$1\",\"status\":\"$2\",\"output\":\"$3\",\"note\":\"$4\"}" >> "$COVERAGE"
}

has() { command -v "$1" >/dev/null 2>&1; }

run_tool() {
  local name="$1"; shift
  if has "$name"; then
    echo "[+] Running $name"
    "$@" 2>>"$OUT/logs/$name.err" | tee -a "$RAW" >/dev/null
    log_method "$name" "ran" "$RAW" "ok"
  else
    echo "$name" >> "$MISSING"
    log_method "$name" "missing" "" "tool not installed"
  fi
}

echo "[*] Starting master subdomain recon..."

while read -r domain; do
  [[ -z "$domain" || "$domain" =~ ^# ]] && continue
  echo "[*] Domain: $domain"

  run_tool subfinder subfinder -d "$domain" -all -silent
  run_tool assetfinder assetfinder --subs-only "$domain"
  run_tool amass amass enum -passive -d "$domain"
  run_tool findomain findomain -t "$domain" -q
  run_tool chaos chaos -d "$domain" -silent

  echo "[+] crt.sh"
  curl -sk "https://crt.sh/?q=%25.$domain&output=json" |
    python3 -c 'import sys,json
try:
 data=json.load(sys.stdin)
 for x in data:
  for n in x.get("name_value","").split("\n"):
   print(n.strip())
except Exception: pass' >> "$RAW"
  log_method "crt.sh" "ran" "$RAW" "certificate transparency"

  echo "[+] alienvault"
  curl -sk "https://otx.alienvault.com/api/v1/indicators/domain/$domain/passive_dns" |
    python3 -c 'import sys,json
try:
 data=json.load(sys.stdin)
 for x in data.get("passive_dns",[]):
  print(x.get("hostname",""))
except Exception: pass' >> "$RAW"
  log_method "alienvault" "ran" "$RAW" "passive dns"

  echo "[+] rapiddns"
  curl -sk "https://rapiddns.io/subdomain/$domain?full=1" |
    grep -Eo "([a-zA-Z0-9_-]+\.)+$domain" >> "$RAW"
  log_method "rapiddns" "ran" "$RAW" "html scrape"

  echo "[+] zone transfer check"
  for ns in $(dig NS "$domain" +short 2>/dev/null); do
    dig axfr "$domain" @"$ns" 2>/dev/null | grep -Eo "([a-zA-Z0-9_-]+\.)+$domain" >> "$RAW"
  done
  log_method "zone_transfer" "ran" "$RAW" "AXFR attempted"

done < "$INPUT"

echo "[*] Cleaning raw results..."
sed 's/\*\.//g' "$RAW" |
  tr '[:upper:]' '[:lower:]' |
  grep -E '^[a-z0-9._-]+\.[a-z]{2,}$' |
  sort -u > "$UNIQ"

echo "[*] Resolving subdomains..."
if has dnsx; then
  dnsx -l "$UNIQ" -silent -a -aaaa -resp-only=false -o "$RESOLVED" 2>>"$OUT/logs/dnsx.err"
  log_method "dnsx_resolution" "ran" "$RESOLVED" "resolved with dnsx"
elif has puredns; then
  puredns resolve "$UNIQ" -w "$RESOLVED" 2>>"$OUT/logs/puredns.err"
  log_method "puredns_resolution" "ran" "$RESOLVED" "resolved with puredns"
else
  while read -r sub; do
    if dig "$sub" +short | grep -qE '[0-9a-fA-F:.]'; then echo "$sub" >> "$RESOLVED"; else echo "$sub" >> "$UNRESOLVED"; fi
  done < "$UNIQ"
  log_method "dig_resolution" "ran" "$RESOLVED" "fallback dig"
fi

echo "[*] Permutation..."
if has dnsgen; then
  dnsgen "$RESOLVED" | sort -u > "$OUT/raw/dnsgen.txt"
  cat "$OUT/raw/dnsgen.txt" >> "$RAW"
  log_method "dnsgen" "ran" "$OUT/raw/dnsgen.txt" "permutation"
else echo "dnsgen" >> "$MISSING"; fi

if has gotator; then
  gotator -sub "$RESOLVED" -silent > "$OUT/raw/gotator.txt" 2>>"$OUT/logs/gotator.err"
  cat "$OUT/raw/gotator.txt" >> "$RAW"
  log_method "gotator" "ran" "$OUT/raw/gotator.txt" "permutation"
else echo "gotator" >> "$MISSING"; fi

if has alterx; then
  alterx -l "$RESOLVED" -silent > "$OUT/raw/alterx.txt" 2>>"$OUT/logs/alterx.err"
  cat "$OUT/raw/alterx.txt" >> "$RAW"
  log_method "alterx" "ran" "$OUT/raw/alterx.txt" "permutation"
else echo "alterx" >> "$MISSING"; fi

echo "[*] CNAME takeover checks..."
while read -r sub; do
  cname=$(dig "$sub" CNAME +short 2>/dev/null | sed 's/\.$//')
  [[ -n "$cname" ]] && echo "$sub $cname" >> "$CNAME"
done < "$UNIQ"

grep -Ei 'github.io|heroku|amazonaws|s3|cloudfront|azurewebsites|azureedge|trafficmanager|wordpress|ghost|tumblr|shopify|myshopify|squarespace|fastly|pantheonsite|zendesk|helpscout|readme.io|webflow|netlify|vercel|surge.sh|fly.dev|render.com|bitbucket.io|gitbook.io|freshdesk|intercom|statuspage|uservoice|wixdns' "$CNAME" > "$TAKEOVER" || true
log_method "cname_takeover_patterns" "ran" "$TAKEOVER" "pattern match"

if has subzy; then
  subzy run --targets "$UNIQ" --hide_fails > "$OUT/takeover/subzy.txt" 2>>"$OUT/logs/subzy.err"
  log_method "subzy" "ran" "$OUT/takeover/subzy.txt" "takeover scanner"
else echo "subzy" >> "$MISSING"; fi

cat "$RAW" "$UNIQ" 2>/dev/null |
  sed 's/\*\.//g' |
  tr '[:upper:]' '[:lower:]' |
  grep -E '^[a-z0-9._-]+\.[a-z]{2,}$' |
  sort -u > "$OUT/all_unique_final.txt"

sort -u "$MISSING" -o "$MISSING"

cat > "$OUT/summary.txt" <<EOF
Subdomain Master Recon Summary
==============================
Raw unique initial : $(wc -l < "$UNIQ" 2>/dev/null || echo 0)
Final unique       : $(wc -l < "$OUT/all_unique_final.txt" 2>/dev/null || echo 0)
Resolved           : $(wc -l < "$RESOLVED" 2>/dev/null || echo 0)
CNAME records      : $(wc -l < "$CNAME" 2>/dev/null || echo 0)
Takeover candidates: $(wc -l < "$TAKEOVER" 2>/dev/null || echo 0)
Missing tools      : $(wc -l < "$MISSING" 2>/dev/null || echo 0)

Important files:
- $OUT/all_unique_final.txt
- $OUT/resolved.txt
- $OUT/takeover/cnames.txt
- $OUT/takeover/candidates.txt
- $OUT/method_coverage.jsonl
- $OUT/missing_tools.txt
EOF

cat "$OUT/summary.txt"
