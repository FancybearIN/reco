# Reco Pipeline Gap Report

## Implemented Real Execution

- `src/recon/recon_chain.py`
  - Subdomain enum: `subfinder`, `assetfinder`, `amass`, `findomain` when installed.
  - DNS resolution: `dnsx`, fallback to `puredns`/`shuffledns` when installed; otherwise carries candidates forward with discarded reason.
  - Permutation: `dnsgen`/`gotator` when installed.
  - Full `httpx` probing over common web ports with JSONL output, alive URL extraction, interesting URL extraction, and tech/category summary.
  - `httpx` results are classified into attack surfaces and validation tasks.

- `src/recon/url_collector.py`
  - URL collection from `gau`, `waybackurls`, and `katana` passive/active when installed.
  - Seeds active crawling from `httpx_alive.txt`.
  - Writes `urls/collected_urls.txt` and `urls/params.txt`.

- `src/intelligence/js_analyzer.py`
  - Downloads scoped JS with timeout/size checks.
  - Extracts JS endpoints and secret candidates.
  - Converts endpoints/secrets into validation tasks and recursive pivots.

- `src/intelligence/api_mapper.py`
  - Builds API inventory from URLs and JS endpoints.
  - Reads `config/session.yaml` account slots.
  - Generates account A/B/unauth/privilege auth matrix tasks and optional live replay helper.

- `src/recon/fuzzing.py`
  - Runs `arjun` when installed and merges parameter inventory.
  - Runs `ffuf` when installed and converts results into content-discovery validation tasks.

- `src/intelligence/nuclei_parser.py`
  - Parses nuclei JSONL output into validation tasks/candidate findings.
  - Keeps nuclei findings as candidates only.

- `src/intelligence/playbook_runner.py`
  - Implements active validation playbook task definitions for required classes.
  - Emits evidence-model candidates without fabricated request/response proof.

- `src/integrations/burp_bridge.py`
  - Imports Burp sitemap/history XML and raw HTTP request files.
  - Converts imported requests into curl, endpoint inventory, parameter inventory, and validation tasks.

- `src/intelligence/methodology_parser.py`
  - Extracts reusable playbook notes, commands, and parameter words from the mandatory local methodology repos.
  - Works offline without Mem0.

- `src/intelligence/pivot_engine.py`
  - Queues every `next_pivots` item back into `tasks/pivot_queue.json`.

- `src/intelligence/validator.py`
  - Enforces a report gate: reproducible request/curl, response proof, impact, false-positive checks, manual validation, and severity.

## Stubbed Or Mocked Logic Found

- Old `recon_chain.py` only ran `subfinder` and wrote target fallback.
- Old `js_analyzer.py` fabricated an AWS key.
- Old `playbook_runner.py` fabricated HTTP response text and marked every hypothesis as a candidate with fake proof.
- Old `validator.py` upgraded candidates based only on presence of request/response/curl/impact.
- Old `surface_classifier.py` classified only basic URL substrings and ignored `httpx`.
- Old `api_mapper.py` only searched for `/api/` strings.

## Missing Or Still Limited Logic

- Live auth-matrix execution is implemented as a helper but defaulted off to avoid using placeholder credentials.
- `ffuf` currently needs a better generated wordlist artifact than the placeholder methodology text path.
- Recursive pivot queue is created, but a long-running worker that drains the queue by pivot type still needs to be connected.
- Shodan/FOFA/GitHub dork/cloud bucket modules were not expanded in this pass beyond existing exposure recon hooks.
- CVE validation remains report-gated task generation; exploit-specific modules should be added per product family.
- Burp JSON exports are not implemented, only common XML sitemap/history and raw HTTP request files.

## Files Edited Or Added

- `src/core/artifacts.py`
- `src/core/pipeline.py`
- `src/recon/recon_chain.py`
- `src/recon/url_collector.py`
- `src/recon/fuzzing.py`
- `src/intelligence/js_analyzer.py`
- `src/intelligence/api_mapper.py`
- `src/intelligence/surface_classifier.py`
- `src/intelligence/hypothesis_engine.py`
- `src/intelligence/playbook_runner.py`
- `src/intelligence/validator.py`
- `src/intelligence/report_builder.py`
- `src/intelligence/methodology_parser.py`
- `src/intelligence/nuclei_parser.py`
- `src/intelligence/pivot_engine.py`
- `src/integrations/burp_bridge.py`

## Exact Implementation Plan

1. Keep `httpx` as the source of live web attack surface and extend category heuristics as real targets show gaps.
2. Feed nuclei JSONL into validation tasks only, then use playbooks for manual confirmation.
3. Replace the temporary ffuf wordlist source with generated methodology wordlists plus tech-specific lists.
4. Run JS extraction on collected/crawled URLs and enqueue every endpoint/secret pivot.
5. Enable live API auth-matrix replay only when non-placeholder credentials exist.
6. Periodically regenerate `playbooks/methodology_playbooks.json` and `fuzz/methodology_params.txt` from local repos.
7. Add product-specific CVE validators for high-value tech surfaced by `httpx`.
8. Connect a worker loop that drains `tasks/pivot_queue.json` by pivot type.
9. Add Burp JSON import support if that export format is used.
10. Keep `findings/reportable.json` empty unless the report gate passes.
