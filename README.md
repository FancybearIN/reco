# BUG BOUNTY — QUICK START REFERENCE
# ============================================================
# Keep this open during every hunt session

## ── FIRST TIME SETUP (run once) ────────────────────────────

bash ~/00_SETUP_RUN_ONCE.sh

# Then copy setup script into your Gemini CLI workspace:
# mv 00_SETUP_RUN_ONCE.sh ~/bugbounty/

## ── NEW TARGET SETUP ────────────────────────────────────────

T="att.com"   # ← change this

# 1. Create target directory from template
cp -r ~/bugbounty/_TARGET_TEMPLATE ~/bugbounty/$T

# 2. Copy agent prompts into target dir
cp ~/bugbounty/GEMINI.md ~/bugbounty/$T/GEMINI.md
cp ~/bugbounty/QWEN.md   ~/bugbounty/$T/QWEN.md

# 3. Paste H1/Bugcrowd scope into:
nano ~/bugbounty/$T/config/scope.txt

# 4. Add test account creds:
nano ~/bugbounty/$T/config/creds.env

# 5. Verify API keys are set:
source ~/bugbounty/config/api-keys.env && echo "Keys: OK"

## ── START GEMINI SESSION ────────────────────────────────────

cd ~/bugbounty/$T
gemini
# Gemini auto-loads GEMINI.md from current directory.
# First thing it does: reads scope.md + handoff/status.md → starts planning.

## ── START QWENCODE SESSION ──────────────────────────────────

cd ~/bugbounty/$T
# In QwenCode: paste contents of QWEN.md as system prompt, then say:
# "T=att.com — start autonomous initialization"

## ── RESUME HUNT (already started) ──────────────────────────

# Gemini:
cd ~/bugbounty/$T && gemini
# → Auto reads handoff/status.md and knows where you stopped

# QwenCode:
# Say: "T=att.com — read gemini-handoff/status.md and continue from last phase"

## ── DAILY WORKFLOW ──────────────────────────────────────────

# Morning: Start QwenCode first
# → QwenCode runs passive/active recon autonomously
# → Updates gemini-handoff/status.md

# Then start Gemini
# → Gemini reads handoff → runs CVE correlation → tasks QwenCode on priority targets

# Evening: Check findings
cat ~/bugbounty/$T/reports/findings.md
cat ~/bugbounty/$T/nuclei/high-critical.txt
cat ~/bugbounty/$T/logs/oob.log | tail -20

## ── KEY FILE REFERENCE ──────────────────────────────────────

# What to check first (priority order):
# 1. ~/bugbounty/TARGET/gemini-handoff/status.md  ← current state
# 2. ~/bugbounty/TARGET/reports/findings.md        ← verified bugs
# 3. ~/bugbounty/TARGET/nuclei/high-critical.txt   ← CVE leads
# 4. ~/bugbounty/TARGET/idor/candidates.md         ← IDOR leads
# 5. ~/bugbounty/TARGET/logs/oob.log               ← blind hits
# 6. ~/bugbounty/TARGET/js/secrets-candidates.txt  ← key leaks

## ── SKILL REFERENCE (for Gemini tasks to QwenCode) ─────────

# passive-recon  → subfinder, gau, waybackurls, crt.sh, github search
# active-recon   → httpx, dnsx, gowitness, panel detection
# js-analyzer    → katana, linkfinder, secretfinder, grep
# cve-hunter     → nuclei cves + exposures + tech-specific + AI correlation
# idor-tester    → cross-account test matrix (needs 2 accounts)
# api-auditor    → auth strip, verb tamper, GraphQL, version downgrade
# business-logic → workflow map, step skip, race condition, param tamper
# oob-monitor    → interactsh setup, SSRF/XXE/blind tests
# noise-filter   → fast triage, reject low-value automatically
# report-builder → HackerOne report format

## ── SHORTHAND CODES ─────────────────────────────────────────

# IDOR-H  = horizontal IDOR (cross-user, same role)
# IDOR-V  = vertical IDOR (low role → high role data)
# BOLA    = API-level object ID manipulation
# PRIVESC = privilege escalation
# ATO     = account takeover chain
# BLIND-SSRF = OOB callback confirmed, impact not proven
# OOB-HIT = interactsh callback received
# LOGIC-SKIP = workflow step bypass
# LOGIC-RACE = race condition on state-changing action
# [V]     = verified finding
# [C]     = candidate (needs more proof)
# [D]     = dead end
# [B]     = blocked (needs scope/auth clarification from Gemini)

## ── CRITICAL RULES ──────────────────────────────────────────

# No impact       → no report
# No PoC          → no report
# Nuclei only     → not a finding (verify with curl)
# Out of scope    → skip immediately
# Real user data  → minimal proof only, redact, stop that path
# Secrets in log  → never
# Stop hunting    → never (pivot, expand, continue)

## ── QUICK TOOL CHECKS ───────────────────────────────────────

# Check all tools available:
for t in subfinder assetfinder amass dnsx httpx katana nuclei ffuf dalfox arjun gau waybackurls anew uro gowitness interactsh-client; do
  command -v $t &>/dev/null && echo "✓ $t" || echo "✗ $t MISSING"
done

# Check OOB listener running:
pgrep -f interactsh-client && echo "OOB: running" || echo "OOB: NOT running"

# Start OOB listener:
T="att.com"
interactsh-client -server oast.pro -v >> ~/bugbounty/$T/logs/oob.log 2>&1 &

# Quick finding count:
T="att.com"
echo "Findings: $(grep -c '^## ' ~/bugbounty/$T/reports/findings.md 2>/dev/null || echo 0)"
echo "Candidates: $(grep -c '^|' ~/bugbounty/$T/idor/candidates.md 2>/dev/null || echo 0)"
echo "CVE leads: $(wc -l < ~/bugbounty/$T/nuclei/high-critical.txt 2>/dev/null || echo 0)"
