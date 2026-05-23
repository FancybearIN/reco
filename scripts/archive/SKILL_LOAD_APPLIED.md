# Skill Load Fix Applied

## What was wrong
- Gemini looked for skills in `./.gemini/skills/` but the directory was empty, so `/skills` returned “No skills available.”
- Custom `.skill` files were not wrapped as Gemini‑style skill folders, so they were ignored.
- Qwen only lists built‑in tool skills because there was no project‑local skill index reference.

## Changes made
1. **Created** `~/reco/.gemini/skills/`.
2. **Symlinked** all existing Gemini‑style skill directories into `.gemini/skills/`:
   - `gemini-skills/skills/*`
   - `gemini-skills/bounty-hunter/bounty-hunter`
   - `gemini-skills/shodan-recon`
3. **Added wrapper folders** for legacy `.skill` files:
   - `legacy-bounty-hunter/SKILL.md` (points to `/home/kali/reco/gemini-skills/shodan-recon/bounty-hunter.skill`)
   - `legacy-shodan-recon/SKILL.md` (points to `/home/kali/reco/gemini-skills/shodan-recon/shodan-recon.skill`)
4. **Regenerated** `SKILLS_INDEX.md` to list all accessible skills and wrappers.
5. **Patched** `files/QWEN.md` and `files/GEMINI.md` with a **Custom Skill Loading** section that documents the index location and the `.gemini/skills/` path.
6. **Backed up** all modified files before changing them in `backup_before_skill_load_fix_20260517_164832/`.

## How to use
- Start Gemini from the workspace (`cd ~/reco && gemini`). Run `/skills` – it will now list the symlinked skills.
- If a skill still does not appear, consult `/home/kali/reco/SKILLS_INDEX.md` and load the skill manually.
- Qwen will still show only built‑in skills, but the added notes remind it (and you) to read `SKILLS_INDEX.md` for custom skills.
- All target output remains under `/home/kali/bugbounty/<target>/` as required.

## Verification commands
```bash
find /home/kali/reco/.gemini/skills -maxdepth 2 -type f -name "SKILL.md" | sort
ls -la /home/kali/reco/.gemini/skills
grep -RIn "Custom Skill Loading" /home/kali/reco/files/GEMINI.md /home/kali/reco/files/QWEN.md
```

Run those commands and you should see the skill files and the new sections.

---
*No further changes were made.*