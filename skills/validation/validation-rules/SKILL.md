---
name: validation-rules
description: Global validation gate for findings, enforcing no‑report rules and checklist.
---

# Validation Rules

## Overview
Provides a centralized checklist that every finding must pass before it can be reported.

## Purpose
- Enforce absolute no‑report conditions.
- Provide a deterministic validation workflow for Qwen Code and Gemini CLI.

## Inputs
- Candidate finding metadata (asset, impact, PoC location, scope confirmation).

## Outputs
- `validated` – true if the finding passes all checks.
- `rejection-reason` – text explaining why a candidate was discarded.

## Core Rules
- **No impact → no report**
- **No PoC → no report**
- **Not working domain → no report**
- **Dead endpoint → no report**
- **Scanner‑only output → no report**
- **Theoretical finding → no report**
- **Public info only → no report**
- **401/403 alone → no report**
- **500 alone → no report**
- **Missing security header alone → no report**
- **Version disclosure alone → no report**
- **Public API key without abuse → no report**
- **Open redirect without useful chain → no report**
- **CORS without credentialed sensitive data → no report**
- **GraphQL introspection alone → no report**
- **Clickjacking without sensitive action → no report**
- **Self‑XSS → no report unless chained to real impact**

## Validation Checklist
1. Asset in scope?
2. Domain resolves?
3. Endpoint live?
4. Behavior reproducible?
5. Impact clear?
6. Working PoC exists?
7. Evidence minimal and safe?
8. Sensitive data redacted?
9. Program policy allows the test?
10. Triager would likely accept?

## Workflow
1. Qwen Code calls this skill with candidate JSON.
2. The skill runs the checklist.
3. Returns `validated:true` or `validated:false` with reason.

## Safety Notes
- Never perform active tests inside this skill; it only evaluates existing data.
- All decisions are logged to `target-research/logs/validation.log`.

## Gemini Handoff
- Write decisions to `target-research/gemini-handoff/status.md` under *Validated Findings* or *Noise* sections.

## Failure Handling
- If any required field is missing, mark as `needs‑gemini‑review`.

## When to Stop
- When a candidate fails any core rule.

## When Not to Report
- Any candidate that does not satisfy the above checklist.
