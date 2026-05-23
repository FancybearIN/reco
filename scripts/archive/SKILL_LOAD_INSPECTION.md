# Skill Load Inspection

## Where custom skills currently reside
- All Gemini‑style skill definitions (`SKILL.md`) are under:
  - `gemini-skills/skills/*/SKILL.md`
  - `gemini-skills/bounty-hunter/bounty-hunter/SKILL.md`
  - `gemini-skills/shodan-recon/SKILL.md`
  - `.skill` files for shodan‑recon live in `gemini-skills/shodan-recon/*.skill`
- The backup folder also contains copies of these, but the live workspace uses the `gemini-skills/` tree.

## Gemini skill loading expectations
- Gemini looks for skill directories inside `./.gemini/skills/` (relative to the current workspace) **or** in the user‑wide `~/.gemini/skills/`.
- Each skill must be a folder that contains a `SKILL.md` file.
- Currently `./.gemini/skills/` does **not** exist; `./.gemini/` is empty, so Gemini reports “No skills available.”
- The `.skill` files are not automatically wrapped as Gemini‑style skills, so they are ignored as well.

## Qwen skill awareness
- Qwen lists only built‑in tool skills (`batch`, `loop`, etc.) because it has no project‑local skill loader.
- There is no `./.qwen/` configuration that points to a skill index, so Qwen cannot discover the custom skills.

## Minimal fix recommendation
1. **Create a local Gemini skill directory** `./.gemini/skills/`.
2. **Symlink** each existing skill folder (the parent folder that contains `SKILL.md`) into `./.gemini/skills/`:
   - `gemini-skills/skills/<skill-name>` → `./.gemini/skills/<skill-name>`
   - `gemini-skills/bounty‑hunter/bounty‑hunter` → `./.gemini/skills/bounty‑hunter`
   - `gemini-skills/shodan-recon` (contains `SKILL.md`) → `./.gemini/skills/shodan-recon`
3. For the two `.skill` files, create thin wrapper directories under `./.gemini/skills/legacy-<name>/` with a generated `SKILL.md` that references the original `.skill` file.
4. **Patch `GEMINI.md`** (already present) to note that skills are loaded from `./SKILLS_INDEX.md` – no functional change needed for loading, but good documentation.
5. **Add a minimal Qwen project config** `./.qwen/config.md` (or comment in `QWEN.md`) stating that the skill index lives at `./SKILLS_INDEX.md` and that custom skills are under `./.gemini/skills/`.
6. **Backup** the affected files before touching them.

These steps are safe, do not move any target output, and give Gemini a proper location to discover the skills. Qwen will still use the index file directly, so its UI will continue to show only built‑ins, but the documentation will make the custom skills available to Qwen scripts.

---
*No files have been modified yet – this file only records the inspection.*