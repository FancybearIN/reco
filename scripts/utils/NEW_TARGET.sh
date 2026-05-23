#!/usr/bin/env bash
# Usage: ./NEW_TARGET.sh <target-domain>
# Creates a new bugbounty target directory under ~/bugbounty/<target>
# and populates it with the standard template structure.

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Error: target domain required"
  echo "Usage: $0 <target-domain>"
  exit 1
fi

TARGET="$1"
BASE="$HOME/bugbounty"
TEMPLATE="$BASE/_template"
TARGET_DIR="$BASE/$TARGET"

if [[ -e "$TARGET_DIR" ]]; then
  echo "Target directory already exists: $TARGET_DIR"
  exit 0
fi

# copy template recursively preserving permissions
cp -a "$TEMPLATE/" "$TARGET_DIR/"

# Copy the latest Gemini Master Prompt
cp "/home/kali/reco/files/GEMINI.md" "$TARGET_DIR/GEMINI.md"
cp "/home/kali/reco/files/QWEN.md" "$TARGET_DIR/QWEN.md"

# ensure script is executable
chmod +x "$0"

echo "Target created: $TARGET_DIR"
echo "Add scope: $TARGET_DIR/scope/scope.txt"
echo "Add files: $TARGET_DIR/files/"
echo "Start Gemini/Qwen from agent workspace."
