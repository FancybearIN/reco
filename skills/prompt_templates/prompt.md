You are Qwen Code operating as my bug bounty skill-builder, recon assistant, and Gemini CLI companion agent.

Context:
I already have existing skill folders similar to:

skills/
  bounty-hunter/
  shodan-recon/

Existing behavior:
- bounty-hunter contains a SKILL.md template/excerpt for building skills.
- shodan-recon contains a professional Shodan recon workflow.
- shodan-recon uses:
  - SKILL.md
  - scripts/
  - references/
  - assets/
  - scripts/shodan_recon.sh
  - scripts/http2_rapid_reset_checker.py
  - scripts/shodan_parse.py
  - scripts/nuclei_runner.sh
- shodan-recon workflow:
  1. Asset discovery through Shodan.
  2. Service probing with httpx.
  3. Vulnerability scanning with nuclei.
  4. Mandatory confirmation using safe PoCs/curl/manual checks.
  5. Markdown report generation.
- shodan-recon enforces:
  - No PoC = no report.
  - Scanner output is not enough.
  - Findings must be reproducible.
  - Safety and authorized-target scanning only.

Your job:
Analyze the existing two skill folders and build a complete reusable bug bounty skill pack using the same style and structure.

The new skills must work for every new target, not only one target.

Primary goal:
Create reusable Qwen Code skills that help with:
- deep recon
- URL collection
- live URL validation
- Wayback/gau usage
- Katana crawling
- SecLists-based fuzzing
- Google dorking
- GitHub dorking
- JS analysis
- GF/pattern-based testing
- API recon
- IDOR/BOLA testing
- auth testing
- upload testing
- nuclei triage
- evidence organization
- report building
- Gemini CLI handoff

Qwen Code role:
Qwen Code is the execution/recon/file-organizing agent.

Gemini CLI role:
Gemini CLI is the strategy/reasoning/validation/report-quality agent.

Both agents may use MCP/tools if configured.

Important:
Use local config files, environment variables, and MCP configuration if available.
Do not hardcode API keys.
Do not print secrets.
Do not leak config values.
Redact API keys, tokens, cookies, Authorization headers, session IDs, and private values.

==================================================
GLOBAL SAFETY + VALIDATION RULES
==================================================

Every skill must enforce these rules:

- Stay strictly in scope.
- Do not test out-of-scope assets.
- Do not perform destructive testing.
- Do not DoS.
- Do not brute force credentials.
- Do not credential stuff.
- Do not spam.
- Do not social engineer.
- Do not exfiltrate real user data.
- Use conservative rate limits.
- Respect bug bounty program policy.
- Scanner output is only a lead.
- Recon output is only a lead.
- Pattern match is only a lead.
- Fuzzing hit is only a lead.
- Google result is only a lead.
- GitHub result is only a lead.
- JS endpoint is only a lead.

Mandatory report gates:

- No impact = no report.
- No PoC = no report.
- Not working domain = no report.
- Dead endpoint = no report.
- Out of scope = no report.
- Scanner-only = no report.
- Theoretical = no report.
- Public info only = no report.
- 401/403 alone = no report.
- 500 alone = no report.
- Missing security header alone = no report.
- Version disclosure alone = no report.
- Public API key without abuse = no report.
- Open redirect without useful chain = no report.
- CORS without credentialed sensitive data = no report.
- GraphQL introspection alone = no report.
- Clickjacking without sensitive action = no report.
- Self-XSS = no report unless chained to real impact.

Before any issue goes into reports/findings.md, it must pass:

1. Asset is in scope.
2. Domain resolves.
3. Endpoint is live.
4. Behavior is reproducible.
5. Impact is clear.
6. Working PoC exists.
7. Evidence is minimal and safe.
8. Sensitive data is redacted.
9. Program policy allows the test.
10. A triager would likely accept it.

If any item fails:
- Put it in reports/noise.md or dead-ends.
- Do not put it in findings.

==================================================
REUSABLE TARGET WORKSPACE STRUCTURE
==================================================

Every new target should use this workspace:

target-research/
  config/
  recon/
  recon/raw/
  recon/processed/
  recon/screenshots/
  urls/
  urls/raw/
  urls/processed/
  js/
  js/raw/
  js/processed/
  params/
  gf/
  fuzzing/
  fuzzing/raw/
  fuzzing/processed/
  nuclei/
  nuclei/raw/
  api/
  graphql/
  auth/
  idor/
  uploads/
  cloud/
  business-logic/
  poc/
  evidence/
  reports/
  reports/drafts/
  reports/final/
  logs/
  scripts/
  wordlists/
  mcp/
  gemini-handoff/

Maintain these files for every target:

target-research/logs/commands.log
target-research/notes.md
target-research/recon/scope.md
target-research/recon/assets.md
target-research/recon/attack-surface.md
target-research/reports/findings.md
target-research/reports/noise.md
target-research/gemini-handoff/status.md

==================================================
SKILL FOLDER STRUCTURE
==================================================

Create every skill like this:

skills/<skill-name>/
  SKILL.md
  scripts/
  references/
  assets/

Each SKILL.md must include:

- Overview
- Purpose
- Inputs
- Outputs
- Core rules
- Workflow
- Tools used
- Example commands
- Validation rules
- Safety notes
- Gemini handoff notes
- Failure handling
- When to stop this skill
- When not to report

Do not create placeholder-only skills.
Each skill must be useful and actionable.

==================================================
SKILLS TO CREATE
==================================================

Create these reusable skills:

1. validation-rules
2. evidence-organizer
3. gemini-handoff-manager
4. recon-orchestrator
5. live-url-prober
6. google-dork-recon
7. github-dork-recon
8. wayback-url-recon
9. katana-crawl-recon
10. interesting-subdomain-finder
11. js-analysis
12. gf-pattern-testing
13. seclists-wordlist-manager
14. fuzzing-engine
15. api-recon
16. graphql-recon
17. idor-bola-tester
18. auth-flow-tester
19. upload-tester
20. nuclei-triage-validator
21. cloud-storage-recon
22. report-builder

Also update or create:

skills/README.md

The README must explain:
- How skills work together.
- Recommended execution order.
- Which skill handles which task.
- How Qwen Code supports Gemini CLI.
- How Gemini should consume Qwen outputs.
- How validation prevents false reports.
- How to add a new skill later.
- How to run these skills on a new target.

==================================================
SKILL DETAILS
==================================================

1. validation-rules

Purpose:
Global validation gate for all findings.

Create:

skills/validation-rules/
  SKILL.md
  references/validation-rules.md

The validation-rules.md file must include:

- Absolute no-report rules.
- Required report checklist.
- False positive filters.
- Scanner triage rules.
- Recon triage rules.
- Fuzzing triage rules.
- Secret exposure validation rules.
- Live domain validation rules.
- Impact questions.
- Triager acceptance questions.

Required text:
No impact = no report.
No PoC = no report.
Not working domain = no report.
Dead endpoint = no report.
Scanner-only = no report.

2. evidence-organizer

Purpose:
Organize PoC evidence safely.

Create script:

skills/evidence-organizer/scripts/create_evidence_case.sh

The script should:
- Create evidence/candidate-NNN/
- Create request.txt
- response.txt
- notes.md
- decision.md
- screenshots/ folder
- Redaction reminder

SKILL.md must enforce:
- redact secrets
- minimal evidence only
- no unnecessary sensitive data
- every candidate gets a decision:
  - verified
  - needs-gemini-review
  - noise
  - dead-end

3. gemini-handoff-manager

Purpose:
Keep Gemini updated with clean summaries.

Create script:

skills/gemini-handoff-manager/scripts/update_handoff.py

It should create/update:

target-research/gemini-handoff/status.md

Format:

# Gemini Handoff Status

## Current Target

## Scope Summary

## Completed Work

## Important Files

## Top Attack Surfaces

## Candidate Bugs Needing Gemini Review

## Verified Findings Ready for Report

## Noise / Dead Ends

## Recommended Next Pivots

4. recon-orchestrator

Purpose:
Master recon controller.

It should call/use:

- live-url-prober
- google-dork-recon
- github-dork-recon
- wayback-url-recon
- katana-crawl-recon
- interesting-subdomain-finder
- js-analysis
- gf-pattern-testing
- seclists-wordlist-manager
- fuzzing-engine
- api-recon
- gemini-handoff-manager

Create script:

skills/recon-orchestrator/scripts/init_target_workspace.sh

It should create target-research/ structure and base files.

5. live-url-prober

Purpose:
Confirm live hosts/URLs before testing.

Create script:

skills/live-url-prober/scripts/probe_live.sh

It should:
- Accept input file of domains/URLs.
- Use dnsx/httpx/curl fallback.
- Save resolved hosts.
- Save live hosts.
- Save dead assets.
- Capture status/title/tech if httpx exists.

Outputs:
- recon/processed/resolved.txt
- recon/processed/live-hosts.txt
- urls/processed/live-urls.txt
- recon/dead-assets.txt

Rules:
Not working domain = no report.
Dead endpoint = no report.

6. google-dork-recon

Purpose:
Search-engine passive recon.

Create:

skills/google-dork-recon/references/google-dorks.md

Include dorks for:
- general surface
- login/admin
- API/docs
- swagger/openapi/graphql
- sensitive files
- cloud storage
- OAuth/SAML/callback
- secrets keywords
- backups/logs

SKILL.md must state:
Google result is not a finding.
Must verify scope/liveness/impact.

7. github-dork-recon

Purpose:
Public code recon.

Create:

skills/github-dork-recon/references/github-dorks.md

Include searches for:
- target domains
- API endpoints
- internal hostnames
- client_secret
- api_key
- access_token
- refresh_token
- Authorization Bearer
- firebase
- supabase
- s3
- graphql
- swagger
- openapi
- webhook
- callback
- redirect_uri
- org_id/workspace_id/tenant_id

Create optional script:

skills/github-dork-recon/scripts/github_search_helper.sh

It may use gh CLI if installed.
It must not print secrets raw.
It must save redacted output.

8. wayback-url-recon

Purpose:
Archive URL collection.

Create script:

skills/wayback-url-recon/scripts/collect_archive_urls.sh

It should use available tools:
- gau
- waybackurls
- katana passive
- urlfinder if available

It should:
- Merge outputs.
- Deduplicate.
- Normalize with uro if available.
- Extract parameterized URLs.
- Extract interesting URLs.
- Save archive live candidates.

Outputs:
- urls/raw/gau.txt
- urls/raw/waybackurls.txt
- urls/processed/archive-all.txt
- urls/processed/archive-interesting.txt
- params/archive-params.txt

Rules:
Archive URL is not a finding.
Old dead URL = no report.
Must verify live endpoint.

9. katana-crawl-recon

Purpose:
Crawl live apps.

Create script:

skills/katana-crawl-recon/scripts/katana_crawl.sh

It should:
- Accept live hosts file.
- Run katana with safe depth/rate.
- Extract URLs.
- Extract JS files.
- Extract API-looking endpoints.
- Save outputs.

Suggested safe command:
katana -list recon/processed/live-hosts.txt -d 3 -silent -jc -kf all -o urls/raw/katana.txt

Outputs:
- urls/raw/katana.txt
- urls/processed/katana-live.txt
- js/processed/katana-js.txt
- api/katana-api-endpoints.txt

10. interesting-subdomain-finder

Purpose:
Prioritize high-value subdomains.

Create:

skills/interesting-subdomain-finder/references/interesting-keywords.txt

Include:
admin
api
app
auth
sso
oauth
saml
login
dashboard
console
portal
internal
dev
staging
stage
test
qa
uat
beta
demo
sandbox
old
legacy
backup
cdn
assets
static
files
upload
download
media
docs
developer
support
billing
payments
invoice
webhook
hooks
graphql
mobile
partner
staff
employee
jira
gitlab
jenkins
grafana
kibana
prometheus
status

Create script:
skills/interesting-subdomain-finder/scripts/rank_subdomains.py

It should rank subdomains by keyword match.

11. js-analysis

Purpose:
Deep JS endpoint/secret/route analysis.

Create script:

skills/js-analysis/scripts/extract_js_endpoints.py

It should:
- Read JS files or JS URL list.
- Extract:
  - URLs
  - API paths
  - GraphQL references
  - WebSocket URLs
  - upload/download endpoints
  - OAuth/callback references
  - cloud storage references
  - possible secrets
  - feature flags
  - role/permission names
- Redact secrets in output.
- Save structured files.

Outputs:
- js/processed/endpoints.txt
- js/processed/routes.md
- js/processed/graphql.md
- js/processed/secrets-review.md
- js/processed/source-maps.md

Rules:
JS endpoint is not a finding.
Client-side key is not a finding unless abuse is proven.

12. gf-pattern-testing

Purpose:
Pattern-based URL classification.

Create script:

skills/gf-pattern-testing/scripts/run_gf_patterns.sh

It should:
- Read urls/processed/all-urls.txt.
- Run gf if installed.
- If gf missing, use fallback grep patterns.
- Create:
  - gf/xss.txt
  - gf/sqli.txt
  - gf/ssrf.txt
  - gf/redirect.txt
  - gf/lfi.txt
  - gf/idor.txt
  - gf/upload.txt
  - gf/download.txt
  - gf/oauth.txt
  - gf/graphql.txt
  - gf/debug.txt
  - gf/interestingparams.txt

Rules:
Pattern match is not a vulnerability.
Send candidates to validation skills.

13. seclists-wordlist-manager

Purpose:
Use SecLists intelligently.

Create:

skills/seclists-wordlist-manager/
  SKILL.md
  scripts/select_wordlist.py
  scripts/seclists_fuzz_plan.sh
  references/seclists-map.md

The skill must:
- Select wordlists by context.
- Prefer small targeted lists first.
- Avoid huge lists unless justified.
- Use conservative rate limits.
- Log which wordlist produced which hits.
- Integrate with fuzzing-engine.

Contexts:
- general-small
- general-medium
- files-small
- api
- params
- admin
- backup
- wordpress
- drupal
- joomla
- laravel
- spring
- nextjs
- graphql

Important SecLists paths to include when present:

/usr/share/seclists/Discovery/Web-Content/raft-small-directories.txt
/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt
/usr/share/seclists/Discovery/Web-Content/raft-small-files.txt
/usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt
/usr/share/seclists/Discovery/Web-Content/common.txt
/usr/share/seclists/Discovery/Web-Content/quickhits.txt
/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt
/usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt
/usr/share/seclists/Discovery/Web-Content/Logins.fuzz.txt
/usr/share/seclists/Discovery/Web-Content/Common-DB-Backups.txt
/usr/share/seclists/Discovery/Web-Content/CMS/wordpress.fuzz.txt

14. fuzzing-engine

Purpose:
Controlled fuzzing.

Create script:

skills/fuzzing-engine/scripts/safe_ffuf.sh

It should:
- Accept target URL with FUZZ.
- Accept context.
- Call seclists-wordlist-manager.
- Use ffuf with conservative rate.
- Save JSON output.
- Filter obvious noise.
- Never report directly.

Rules:
- Fuzzing hit is not a finding.
- 200/403/500 alone is not a report.
- Validate manually.

15. api-recon

Purpose:
REST API inventory and testing preparation.

Create:
skills/api-recon/scripts/build_api_inventory.py

It should:
- Read URLs from JS/Katana/Wayback/fuzzing.
- Extract API endpoints.
- Group by host/version.
- Identify object-ID endpoints.
- Identify sensitive actions.
- Identify auth endpoints.
- Create IDOR candidate list.

Outputs:
- api/inventory.md
- api/endpoints.txt
- api/object-id-endpoints.txt
- api/sensitive-actions.md
- api/idor-candidates.md

16. graphql-recon

Purpose:
GraphQL discovery and safe analysis.

Create:
skills/graphql-recon/SKILL.md
skills/graphql-recon/references/graphql-checklist.md

Include:
- endpoint discovery
- introspection only if allowed
- authz testing
- batching
- aliases
- node/global ID
- query/mutation inventory
- excessive data exposure
- depth/cost only if allowed and safe

Rules:
GraphQL introspection alone = no report.
Need impact and PoC.

17. idor-bola-tester

Purpose:
Validate IDOR/BOLA/access control.

Create:
skills/idor-bola-tester/references/idor-test-matrix.md

Include tests:
- User A object as User A
- User A object as User B
- Org A object as Org B
- admin action as member
- member action as viewer
- method swap
- body/path ID mismatch
- parameter pollution
- mass assignment
- old API version
- mobile endpoint difference
- deleted object access
- invite ID abuse
- file/invoice/export/report IDOR

Rules:
ID in URL is not a bug.
Must prove unauthorized access/action.
No impact = no report.
No PoC = no report.

18. auth-flow-tester

Purpose:
Authentication and account lifecycle testing.

Create:
skills/auth-flow-tester/references/auth-checklist.md

Include:
- signup
- login
- logout
- password reset
- password change
- email change
- email verification
- MFA setup/removal
- OAuth
- SAML/SSO
- magic links
- invite links
- account linking
- session refresh
- JWT
- duplicate registration/twinning
- email canonicalization
- Unicode/case normalization

Rules:
No brute force.
No spam.
Need account/security impact.

19. upload-tester

Purpose:
Upload/download/file processing testing.

Create:
skills/upload-tester/references/upload-checklist.md

Include:
- SVG XSS
- HTML upload
- MIME bypass
- double extension
- case bypass
- filename path traversal
- Unicode filename
- metadata injection
- CSV formula injection with realistic impact
- ZIP slip if extraction exists
- PDF/HTML rendering injection
- URL import SSRF
- unauthorized file download
- signed URL weakness
- file overwrite
- public bucket exposure

Rules:
Extension bypass alone = no report.
Need execution/access/SSRF/overwrite/sensitive exposure/impact.

20. nuclei-triage-validator

Purpose:
Validate nuclei results.

Create:
skills/nuclei-triage-validator/scripts/triage_nuclei.py

It should:
- Read nuclei JSON/markdown output.
- Group by severity/template.
- Mark as needs manual validation.
- Create triage file.
- Never auto-add to findings.

Rules:
Nuclei result is not a finding.
Template severity is not final severity.
Manual verification required.

21. cloud-storage-recon

Purpose:
Cloud asset discovery and safe validation.

Create:
skills/cloud-storage-recon/references/cloud-checklist.md

Include:
- S3
- GCS
- Azure Blob
- Firebase
- Supabase
- public read
- public write
- sensitive files
- exposed backups
- exposed logs
- token reuse
- CORS/storage policy
- signed URL weakness

Rules:
Cloud URL alone = no report.
Need sensitive data, write access, auth bypass, or abuse impact.

22. report-builder

Purpose:
Build clean final reports only from verified findings.

Create:
skills/report-builder/scripts/build_report.py

It should:
- Read verified finding drafts.
- Ensure checklist exists.
- Refuse to finalize if:
  - no impact
  - no PoC
  - no live endpoint
  - no scope confirmation
  - no evidence
- Output markdown report under reports/final/

Report format:

# Finding: TITLE

## Severity

## Affected Asset

## Summary

## Impact

## Preconditions

## Steps to Reproduce

## Proof of Concept

## Evidence

## Root Cause Hypothesis

## Remediation

## Retest Notes

## Scope/Safety Notes

## Validation Checklist

==================================================
REQUIRED SCRIPT QUALITY
==================================================

Scripts must be:

- Safe by default.
- Configurable.
- Conservative with rate limits.
- Able to run repeatedly.
- Not dependent on one exact environment.
- Using fallbacks when tools are missing.
- Clear in output.
- Logging useful actions.
- Not printing secrets.

Use Bash or Python.

Where tools may be missing:
- Detect tool with command -v.
- If missing, log and skip or use fallback.
- Do not crash the whole workflow unless the input is invalid.

==================================================
GEMINI + QWEN WORKFLOW
==================================================

Create docs in skills/README.md explaining this workflow:

Qwen Code:
- Builds and runs recon.
- Uses tools.
- Processes output.
- Organizes evidence.
- Creates candidate lists.
- Updates gemini-handoff/status.md.
- Drafts reports only after validation.

Gemini CLI:
- Reads gemini-handoff/status.md.
- Reviews high-value assets.
- Reviews candidates.
- Decides next pivots.
- Validates impact reasoning.
- Improves report quality.
- Rejects weak/no-impact issues.

Required handoff cycle:

1. Qwen runs recon skill.
2. Qwen updates handoff.
3. Gemini reviews and chooses next test path.
4. Qwen executes validation/test.
5. Qwen organizes evidence.
6. Gemini reviews impact.
7. If valid, Qwen builds draft report.
8. Gemini polishes final report.

==================================================
NEW TARGET EXECUTION FLOW
==================================================

skills/README.md must include this reusable flow:

For every new target:

1. Create target workspace:
   recon-orchestrator/scripts/init_target_workspace.sh TARGET

2. Add scope:
   target-research/recon/scope.md

3. Run passive recon:
   wayback-url-recon
   google-dork-recon
   github-dork-recon

4. Probe live assets:
   live-url-prober

5. Crawl:
   katana-crawl-recon

6. Analyze JS:
   js-analysis

7. Classify URLs:
   gf-pattern-testing

8. Fuzz safely:
   fuzzing-engine with seclists-wordlist-manager

9. Build API inventory:
   api-recon

10. Prioritize:
   interesting-subdomain-finder
   gemini-handoff-manager

11. Validate:
   idor-bola-tester
   auth-flow-tester
   upload-tester
   graphql-recon
   cloud-storage-recon
   nuclei-triage-validator

12. Organize evidence:
   evidence-organizer

13. Build report:
   report-builder

14. Gemini reviews final report.

==================================================
FINAL ACTIONS
==================================================

Now perform the work.

Step 1:
Inspect existing skills/bounty-hunter and skills/shodan-recon folders if they exist.

Step 2:
Extract their structure and style.

Step 3:
Create all new skill folders listed above.

Step 4:
Write complete SKILL.md files for each.

Step 5:
Write scripts and references.

Step 6:
Create skills/README.md.

Step 7:
Print a final summary showing:
- Created skills
- Created scripts
- Created references
- How to run on a new target
- Any missing external tools detected

Do not ask for confirmation.
Do not stop after creating only placeholders.
Build useful reusable skills.
