---
name: recon-orchestrator
description: Master controller that orchestrates all recon sub‑skills and prepares the target workspace.
---

# Recon Orchestrator

## Overview
Initialises the per‑target workspace and coordinates the execution of all downstream recon and validation skills.

## Purpose
- Create a standardised `target-research/` directory tree.
- Seed base files (`logs/commands.log`, `notes.md`).
- Provide a single entry point for Qwen Code to launch the full recon pipeline.

## Inputs
- Target identifier (e.g., `example.com` or a friendly name).

## Outputs
- Fully populated `target-research/` hierarchy.
- Empty placeholder files ready for the other skills.

## Workflow
1. `init_target_workspace.sh <target>` is called.
2. Directory tree from the specification is created.
3. Base markdown files (`scope.md`, `assets.md`, `attack-surface.md`, `findings.md`, `noise.md`, `status.md`) are touched.
4. A log entry is written to `target-research/logs/commands.log`.

## Safety Notes
- No network activity is performed – only filesystem operations.
- All paths are resolved under the current project root to avoid accidental writes outside the workspace.

## Gemini Handoff
- After initialisation, the orchestrator signals Gemini via the handoff manager to note that a new target workspace exists.

## Failure Handling
- If any directory cannot be created, the script aborts with a clear error and logs the failure.

## When to Stop
- After the workspace is ready; subsequent recon steps are executed by their own skills.

## When Not to Report
- This skill never generates findings; it only prepares the environment.
