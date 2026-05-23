# Reco Skills

This folder contains Gemini CLI skill definitions and prompt templates.

## Structure

- `recon/`: Skills for domain and asset discovery.
- `validation/`: Rules and logic for finding verification.
- `reporting/`: Evidence organization and report generation.
- `memory/`: Logic for handoffs and persistent memory updates.
- `prompt_templates/`: Base templates for AI interactions.

## Usage for Gemini CLI

- **Activation**: Use `activate_skill` with the skill name to load specialized guidance.
- **Validation**: Refer to `validation/` when evaluating if a finding is reportable.

> ⚠️ **Warning**: These markdown files define your operational boundaries. Read them carefully before performing tasks in their respective domains.
