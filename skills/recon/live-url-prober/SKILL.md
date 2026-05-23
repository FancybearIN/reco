---
name: live-url-prober
description: Validates that discovered domains and URLs are alive before any active testing.
---

# Live URL Prober

## Overview
Confirms host resolution and HTTP availability for a list of URLs or domains, producing separate lists of live, dead, and resolved assets.

## Purpose
- Prevent out‑of‑scope or dead endpoints from entering the testing pipeline.
- Provide additional tech‑stack hints (via `httpx` when available).

## Inputs
- Path to a file containing one URL or domain per line (e.g., `urls/raw/combined.txt`).

## Outputs
- `recon/processed/resolved.txt` – hostnames that resolved via DNS.
- `recon/processed/live-hosts.txt` – domains that responded to a TCP handshake.
- `urls/processed/live-urls.txt` – full URLs that returned a successful HTTP response.
- `recon/dead-assets.txt` – list of dead domains/URLs with failure reason.

## Workflow
1. The script checks for `dnsx`, then `httpx`, finally falls back to `curl`.
2. DNS resolution results are written to `resolved.txt`.
3. HTTP probing results (status code, title, tech) are written to `live-urls.txt` (if `httpx` is present) or a simple `curl`‑based list.
4. Failures are captured in `dead-assets.txt`.
5. All actions are logged to `target-research/logs/commands.log`.

## Safety Notes
- Only read‑only probes; no payloads are sent.
- Rate limited to 20 concurrent checks (configurable via `MAX_CONCURRENCY`).
- No authentication credentials are used.

## Gemini Handoff
- Appends a concise summary of live hosts to the *Current Target* section via the Gemini handoff manager.

## Failure Handling
- If none of the probing tools are installed, the script aborts with a clear message and logs the issue.

## When to Stop
- After all input entries have been classified as live or dead.

## When Not to Report
- Any asset that appears only in `dead-assets.txt` is excluded from downstream findings.
