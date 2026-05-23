#!/usr/bin/env bash
set -euo pipefail

URLS="${1:-}"
OUTDIR="${2:-nuclei-out}"

if [[ -z "$URLS" || ! -f "$URLS" ]]; then
  echo "Usage: $0 live_urls.txt output_dir"
  exit 1
fi

mkdir -p "$OUTDIR"

echo "[+] Running priority nuclei templates..."

nuclei -l "$URLS" \
  -tags exposure,misconfig,cve,default-login,token,backup,debug,panel \
  -severity medium,high,critical \
  -rl 5 \
  -c 10 \
  -jsonl \
  -o "$OUTDIR/nuclei-priority.jsonl"

echo "[+] Running general nuclei templates..."

nuclei -l "$URLS" \
  -severity low,medium,high,critical \
  -rl 5 \
  -c 10 \
  -jsonl \
  -o "$OUTDIR/nuclei.jsonl"
