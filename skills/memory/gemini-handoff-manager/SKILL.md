---
name: gemini-handoff-manager
description: Keeps Gemini CLI updated with clean summaries of progress, findings, and next steps.
---

# Gemini Handoff Manager

## Overview
Maintains `target-research/gemini-handoff/status.md` with concise sections for scope, completed work, attack surfaces, candidate bugs, verified findings, noise, and recommended pivots.

## Purpose
- Provide Gemini CLI a single source of truth for handoff.
- Auto‑append updates after each major skill runs.

## Inputs
- Section name (e.g., *Validated Findings*).
- Markdown content to append.

## Outputs
- Updated `status.md` file.

## Workflow
1. Qwen Code calls `update_handoff.py` with a JSON payload `{section: "...", content: "..."}`.
2. Script creates the file if missing, ensures headings exist, appends content under the appropriate heading.
3. Logs action to `target-research/logs/commands.log`.

## Safety Notes
- Never includes raw secrets; scripts redact any `Authorization:` or similar strings before writing.
- Idempotent – repeated calls with the same content are ignored.

## Example Usage
```bash
python3 skills/gemini-handoff-manager/scripts/update_handoff.py --section "Verified Findings" --content "- CVE‑2023‑44487 on app.example.com" 
```

## Failure Handling
- If the target workspace does not exist, the script aborts with a clear error.
- Missing section headings are created automatically.

## When to Stop
- After the latest findings or pivots are recorded.

## When Not to Report
- Do not write unverified or noisy candidates; they belong in the *Noise* section.
