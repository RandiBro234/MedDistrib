# MedDistrib — Agent Guide

## Run

```powershell
venv\Scripts\activate; python app.py
```

Opens on `http://127.0.0.1:5000`. No other build/test/lint steps exist.

## Project structure

- `app.py` — single Flask route (`GET`/`POST` on `/`)
- `model/` — recommendation engines (CB cosine similarity, KB priority scoring, hybrid weighted combo)
- `static/` — Leaflet map + CSS + GeoJSON
- `data/` — BPS 2025 source CSVs, `dataset_final.csv` (38 real + 196 augmented rows), `dataset_scaled.csv` (MinMax-scaled), `goverment.ipynb` (data prep notebook)

## Gotchas

- Python 3.12.3, venv is at `venv/`.
- `selected` province reads from **query param first**, then form, defaults to `"ACEH"` (`app.py:44`).
- GeoJSON province names are normalized in `static/js/map.js` via `normalizeProvinceName()` (e.g., "DAERAH ISTIMEWA YOGYAKARTA" -> "DI YOGYAKARTA"). The Flask dataset uses the shorter names — map clicks use query param `?provinsi=...`.
- Augmented data (5 variants per province with 0.85–1.15 noise) exists only for training; `get_real_provinces()` filters these out (excludes `_VAR` suffix and `INDONESIA`).
- `cloudflared` binary in root is a Linux Cloudflare Tunnel binary, not part of the app.

## No CI/CD, no tests, no linter/formatter/typechecker
