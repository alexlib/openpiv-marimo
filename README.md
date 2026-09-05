# piv-marimo

Minimal marimo boilerplate for PIV parameter tuning + batch processing, built to
run everywhere: desktop (`marimo edit`), local web server (`marimo run`), or
fully static/serverless in-browser via WASM export (Pyodide).

## Why this shape

- **One notebook** (`app.py`), multi-column layout: Setup → Tuning → Batch → Results.
- **`core/` is UI-agnostic** — pure Python, no marimo imports — so it stays usable
  from a future CLI or a different UI without rewriting the compute logic.
- **Image source is pluggable**: local file upload (works everywhere, including
  WASM) or a public/signed URL fetch (for Google Cloud Storage objects) behind
  one `load_pair()` call. WASM/Pyodide cannot browse a local folder or use the
  `google-cloud-storage` auth client, so both paths go through plain HTTP
  bytes-in, bytes-out to work identically in every mode.
- **Single-pass vs multi-pass** is one data structure (a list of "pass" configs),
  not two separate code paths — multi-pass is just `len(passes) > 1`.
- **Batch is button-gated** (`mo.ui.run_button`) so tuning sliders never
  accidentally trigger a full dataset run.

## Run locally (full Python, fastest, real openpiv-python)

```bash
pip install -r requirements.txt
marimo edit app.py       # interactive editing
marimo run app.py        # app mode, local server
```

## Export to static WASM (no server, open `index.html` anywhere)

```bash
marimo export html-wasm app.py -o dist --mode run
```

`dist/` is a static site — host it on GitHub Pages, Cloudflare Pages, S3, or
just open it locally. First load pulls the Pyodide runtime + packages, so it's
slower to start and slower per-correlation than native Python. Verify
`openpiv` and `pivpy` actually resolve as Pyodide wheels before relying on this
path for real analysis; if they don't, `core/piv.py`'s pure-numpy fallback
still runs.

## Layout

```
core/          UI-agnostic: image IO, pass/validation config, PIV compute
app.py         marimo notebook (multi-column UI)
requirements.txt
```

## Known limits of the WASM path (by design, not a bug to fix)

- No local folder browsing — file upload widget only.
- No `google-cloud-storage` client auth — GCS access is a plain HTTPS GET on a
  public or signed URL.
- Heavier multi-pass correlation over many pairs will be slow; use it for
  single-pair tuning and small batches, not large production runs.
