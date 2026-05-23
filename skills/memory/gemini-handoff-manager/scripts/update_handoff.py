#!/usr/bin/env python3
import sys, argparse, os, json, re

def load_status(path):
    if not os.path.exists(path):
        return "# Gemini Handoff Status\n\n"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_status(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def ensure_heading(content, heading):
    pattern = rf"^##\s+{re.escape(heading)}$"
    if re.search(pattern, content, flags=re.MULTILINE):
        return content
    return content.rstrip() + f"\n## {heading}\n\n"

def append_section(content, heading, new_text):
    content = ensure_heading(content, heading)
    # Find heading position
    split = re.split(rf"^(##\s+{re.escape(heading)}\s*)$", content, flags=re.MULTILINE)
    # split gives ['', '## Heading', rest]
    if len(split) >= 3:
        before = split[0]
        header = split[1]
        after = split[2]
        # Append if not already present
        if new_text.strip() not in after:
            after = after.rstrip() + "\n" + new_text.strip() + "\n"
        return before + header + after
    return content + f"\n## {heading}\n{new_text}\n"

def redact(text):
    # simple redaction of Authorization headers and tokens
    text = re.sub(r"Authorization:\s*[^\n]+", "Authorization: <REDACTED>", text, flags=re.IGNORECASE)
    text = re.sub(r"(?i)Bearer\s+[A-Za-z0-9._-]+", "Bearer <REDACTED>", text)
    return text

def main():
    parser = argparse.ArgumentParser(description="Update Gemini handoff status file")
    parser.add_argument("--section", required=True, help="Section heading to update")
    parser.add_argument("--content", required=True, help="Markdown content to append")
    parser.add_argument("--status-path", default="target-research/gemini-handoff/status.md", help="Path to status file")
    args = parser.parse_args()

    status_path = os.path.abspath(args.status_path)
    os.makedirs(os.path.dirname(status_path), exist_ok=True)
    current = load_status(status_path)
    safe_content = redact(args.content)
    updated = append_section(current, args.section, safe_content)
    save_status(status_path, updated)
    # Log action
    log_path = os.path.abspath("target-research/logs/commands.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[handoff] Updated section '{args.section}'\n")

if __name__ == "__main__":
    main()
