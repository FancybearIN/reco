# Workspace Inspection

## Agent Workspace Root
- **Path:** `/home/kali/reco`
- Contains reusable agent code, prompts, and skills.

## Reusable Skill & Prompt Folders
- `./gemini-skills/skills/` – skill definitions (`SKILL.md` files).
- `./gemini-skills/bounty-hunter/` – bounty‑hunter skill.
- `./gemini-skills/shodan-recon/` – shodan‑recon skill and related scripts.
- `./files/` – core prompt files (`GEMINI.md`, `QUICK_START.md`, `QWEN.md`).
- `./gemini-skills/prompt.md` – master prompt for the agent.

## Old Target Output Mixed In
The workspace also contains legacy target data, primarily for the AT&T program:
- `./gemini-skills/shodan-recon/recon-att.com/` (raw recon files, reports, etc.)
- `./gemini-skills/shodan-recon/target‑research/` (generic old output hierarchy)
- Various scripts in `00_SETUP_RUN_ONCE.sh` that reference `~/bugbounty/TARGET/...` paths.
- References throughout `GEMINI.md`, `QWEN.md`, `QUICK_START.md`, and other helper scripts that hard‑code `TARGET` or `att.com`.

## What Should Remain in the Workspace
- All **skill definitions** and **prompt files**.
- Configuration and helper scripts that do **not** embed a concrete target path.
- The `map.txt` mapping file.
- Any reusable utility scripts inside `gemini-skills/**/scripts/`.

## What Must Not Be Used for New Targets
- Any folder under `./gemini-skills/**/recon‑att.com`.
- The generic `target‑research/` hierarchy inside the workspace.
- Hard‑coded references to `~/bugbounty/TARGET/...` or specific domains (e.g., `att.com`).
- Existing `00_SETUP_RUN_ONCE.sh` path constants that assume a target exists in the workspace.

## Files Requiring Path Edits
The following files contain hard‑coded old output paths and will need to be updated to use the new `$TARGET` variable pointing to `~/bugbounty/<target>/`:
- `./files/00_SETUP_RUN_ONCE.sh` (many lines referencing `~/bugbounty/TARGET/...`).
- `./files/GEMINI.md` (mentions `~/bugbounty/TARGET/...`).
- `./files/QWEN.md` (contains many `$T`/`$TARGET` paths).
- `./files/QUICK_START.md` (example commands with `T="att.com"`).
- Any `SKILL.md` or scripts under `gemini-skills/**` that reference `target-research/` or `recon-att.com`.

## Next Steps
1. **Backup** the important configuration/prompt/skill files (Phase 2).
2. **Create** the new output root `~/bugbounty/` and template structure (Phase 3).
3. **Update** scripts and documentation to use the new `$TARGET` layout and remove AT&T‑specific paths (Phase 4‑7).
4. **Document** legacy folders in `OLD_OUTPUT_FOLDERS.md` (Phase 9).
5. Verify everything and generate `OUTPUT_REFACTOR_DONE.md` (Phase 10).

*No modifications have been made yet; this file is for inspection only.*