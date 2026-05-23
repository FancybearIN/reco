---
name: evidence-organizer
description: Organizes PoC evidence into structured cases and enforces redaction and decision workflow.
---

# Evidence Organizer

## Overview
Creates a reproducible evidence package for each candidate finding, ensuring minimal sensitive data is retained and decisions are recorded.

## Purpose
- Standardize evidence layout.
- Enforce redaction of secrets.
- Track verification status.

## Inputs
- Candidate identifier (e.g., `candidate-001`).
- Paths to raw request/response files.

## Outputs
- Directory `evidence/candidate-###/` containing:
  - `request.txt`
  - `response.txt`
  - `notes.md`
  - `decision.md` (values: `verified`, `needs-gemini-review`, `noise`, `dead-end`).
  - `screenshots/` folder.

## Workflow
1. Qwen Code runs `create_evidence_case.sh` with a candidate ID.
2. The script scaffolds the directory structure.
3. Analyst adds request/response data and fills `notes.md`.
4. Run `decision.md` to record outcome.

## Safety Notes
- Do **not** store raw secrets; redact them before saving.
- Keep evidence size minimal—only what is needed to reproduce the PoC.

## Gemini Handoff
- Summarize each case in `target-research/gemini-handoff/status.md` under *Evidence*.

## Failure Handling
- If a required file is missing, mark the case as `needs-gemini-review`.

## When to Stop
- After evidence is collected and decision recorded.

## When Not to Report
- Cases marked `noise` or `dead-end` are excluded from final reports.
