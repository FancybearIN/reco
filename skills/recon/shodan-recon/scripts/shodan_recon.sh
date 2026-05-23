#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 target.com"
  exit 1
fi

OUT="recon-${TARGET}"
mkdir -p "$OUT"/{shodan,extracted,httpx,nuclei}

echo "[+] Target: $TARGET"
echo "[+] Output: $OUT"

need_tool() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[-] Missing tool: $1"
    return 1
  fi
}

echo "[+] Checking tools..."
need_tool shodan || true
need_tool jq || true
need_tool httpx || true
need_tool nuclei || true

echo "[+] Checking Shodan auth..."
if ! shodan info >/dev/null 2>&1; then
  echo "[-] Shodan CLI not configured."
  echo "Run: shodan init <API_KEY>"
  exit 1
fi

run_shodan() {
  local name="$1"
  local query="$2"
  local outfile="$OUT/shodan/${name}.txt"

  echo "[+] Shodan query: $query"

  shodan search \
    --limit 1000 \
    --fields ip_str,port,hostnames,org,asn,product,version,vulns,http.title \
    "$query" > "$outfile" || true
}

echo "[+] Running shodan domain..."
shodan domain "$TARGET" > "$OUT/shodan/domain.txt" || true

run_shodan "hostname" "hostname:${TARGET}"
run_shodan "cert-cn" "ssl.cert.subject.cn:${TARGET}"
run_shodan "cert-san" "ssl.cert.subject.alt_names:${TARGET}"
run_shodan "html" "http.html:\"${TARGET}\""
run_shodan "title" "http.title:\"${TARGET}\""
run_shodan "vulns" "hostname:${TARGET} has_vuln:true"

run_shodan "port-80" "hostname:${TARGET} port:80"
run_shodan "port-443" "hostname:${TARGET} port:443"
run_shodan "port-8080" "hostname:${TARGET} port:8080"
run_shodan "port-8443" "hostname:${TARGET} port:8443"
run_shodan "port-8000" "hostname:${TARGET} port:8000"
run_shodan "port-3000" "hostname:${TARGET} port:3000"
run_shodan "port-5000" "hostname:${TARGET} port:5000"
run_shodan "port-9000" "hostname:${TARGET} port:9000"

run_shodan "jenkins" "hostname:${TARGET} product:\"Jenkins\""
run_shodan "grafana" "hostname:${TARGET} product:\"Grafana\""
run_shodan "kibana" "hostname:${TARGET} product:\"Kibana\""
run_shodan "mongodb" "hostname:${TARGET} product:\"MongoDB\""
run_shodan "redis" "hostname:${TARGET} product:\"Redis\""
run_shodan "elastic" "hostname:${TARGET} product:\"Elasticsearch\""
run_shodan "kubernetes" "hostname:${TARGET} product:\"Kubernetes\""
run_shodan "docker" "hostname:${TARGET} product:\"Docker\""
run_shodan "gitlab" "hostname:${TARGET} product:\"GitLab\""
run_shodan "nexus" "hostname:${TARGET} product:\"Nexus Repository Manager\""
run_shodan "artifactory" "hostname:${TARGET} product:\"Artifactory\""

run_shodan "docker-api" "hostname:${TARGET} port:2375"
run_shodan "docker-tls" "hostname:${TARGET} port:2376"
run_shodan "k8s-api" "hostname:${TARGET} port:6443"
run_shodan "kubelet" "hostname:${TARGET} port:10250"
run_shodan "redis-port" "hostname:${TARGET} port:6379"
run_shodan "mongo-port" "hostname:${TARGET} port:27017"
run_shodan "elastic-port" "hostname:${TARGET} port:9200"

echo "[+] Combining raw Shodan output..."
cat "$OUT"/shodan/*.txt 2>/dev/null > "$OUT/shodan/raw_all.txt" || true

echo "[+] Parsing Shodan output..."
python3 "$(dirname "$0")/shodan_parse.py" "$OUT" "$TARGET"

echo "[+] Building URL list..."
: > "$OUT/extracted/urls.txt"

if [[ -s "$OUT/extracted/subdomains.txt" ]]; then
  while read -r sub; do
    echo "https://${sub}"
    echo "http://${sub}"
  done < "$OUT/extracted/subdomains.txt" >> "$OUT/extracted/urls.txt"
fi

if [[ -s "$OUT/extracted/ip_ports.txt" ]]; then
  while read -r ipport; do
    port="${ipport##*:}"
    if [[ "$port" == "443" || "$port" == "8443" ]]; then
      echo "https://${ipport}"
    else
      echo "http://${ipport}"
    fi
  done < "$OUT/extracted/ip_ports.txt" >> "$OUT/extracted/urls.txt"
fi

sort -u "$OUT/extracted/urls.txt" -o "$OUT/extracted/urls.txt"

echo "[+] Probing with httpx..."
if command -v httpx >/dev/null 2>&1 && [[ -s "$OUT/extracted/urls.txt" ]]; then
  httpx -l "$OUT/extracted/urls.txt" \
    -title \
    -tech-detect \
    -status-code \
    -follow-redirects \
    -location \
    -content-length \
    -web-server \
    -ip \
    -cdn \
    -json \
    -o "$OUT/httpx/httpx.json" || true

  jq -r '.url // empty' "$OUT/httpx/httpx.json" 2>/dev/null | sort -u > "$OUT/httpx/live_urls.txt" || true
else
  echo "[-] httpx missing or no URLs found."
fi

echo "[+] Running nuclei priority templates..."
if command -v nuclei >/dev/null 2>&1 && [[ -s "$OUT/httpx/live_urls.txt" ]]; then
  nuclei -l "$OUT/httpx/live_urls.txt" \
    -tags exposure,misconfig,cve,default-login,token,backup,debug,panel \
    -severity medium,high,critical \
    -rl 5 \
    -c 10 \
    -jsonl \
    -o "$OUT/nuclei/nuclei-priority.jsonl" || true
else
  echo "[-] nuclei missing or no live URLs found."
fi

echo "[+] Generating report..."
python3 "$(dirname "$0")/shodan_parse.py" "$OUT" "$TARGET" --report

echo "[+] Done."
echo "[+] Report: $OUT/report.md"
