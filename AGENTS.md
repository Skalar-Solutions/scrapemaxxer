# AGENTS.md

## Setup
- Python venv di `.venv` (Python 3.14). Aktifkan: `source .venv/bin/activate`.
- Scrapling `0.4.15` + extras `[ai]`. Install ulang: `pip install -r requirements.txt`.
- MCP scrapling terdaftar di `opencode.json` (`.venv/bin/scrapling-mcp`).

## Mesin ini (macOS 12, Intel)
- **HTTP fetcher jalan.** Browser fetcher (`dynamic`/`stealthy`) TIDAK bisa — Playwright >=1.62 tidak support macOS 12. Butuh macOS 13+ / PC.
- `curl_cffi` butuh `DYLD_INSERT_LIBRARIES=SystemConfiguration` di macOS <=12; sudah di-bake di `.venv/bin/activate`, jadi WAJIB `source .venv/bin/activate` sebelum jalan python.
- `cryptography` di-pin `<49` (>=49 tidak ada wheel cp314 untuk Intel mac).
- MCP browser tools (`fetch`, `stealthy_fetch`) akan gagal di mesin ini; `make_request`/`bulk_get` jalan.

## Usage
- CLI: `python main.py <url> [-s selector] [-i name=selector] [-o file]`
- Profil preset: `python main.py <url> --profile seo|geo|aeo|all [--solve-cf]`
- Test: `python test_extractor.py` (assert-based, no framework)
- Pilih fetcher via `FETCHER=http|dynamic|stealthy` di `.env`.
- Hasil scrape masuk `output/` (gitignored).
