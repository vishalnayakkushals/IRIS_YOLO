# IRIS_YOLO — Change Ledger

---

## AI Handover Note
> **Read this first before making any changes.**
> This section is updated with every major change so any AI agent or developer can pick up exactly where work left off.

### Current State (as of 2026-05-14)
- Project is **fully working end-to-end** in local Windows environment
- First real scan completed: RRNAGAR BLR / 2026-05-14 → 66 images, 52 relevant uploaded, 0 failures
- All infrastructure is live: RDS tables created, S3 access confirmed, GitHub synced

### What this project does
Reads store camera images from S3, runs YOLOv8s person detection, uploads only relevant images back to S3 under a `relevant image/` subfolder, and saves scan metadata to PostgreSQL.

### Architecture in one line
`run.py` → `processor.py` → [`s3_io.py` + `yolo_detector.py` + `db.py`]

### Critical facts for any AI agent continuing this work
1. **S3 bucket:** `middle-ware` (ap-south-1). Same bucket for input and output.
2. **Input key pattern:** `iris/<store_s3_code>/<date_folder>/<HH-MM-SS_CameraID-Frame.jpg>`
3. **Output key pattern:** `iris/<store_s3_code>/relevant image/<date_folder>/<filename.jpg>`
4. **Date folder format in S3 is variable** (e.g. `14-05-26`, `2026-05-14`). The `find_date_folder()` in `s3_io.py` auto-detects any format — never hardcode date format.
5. **DB host:** `pba-rds.cpca96t4u31g.ap-south-1.rds.amazonaws.com`, DB: `iris-db`, user: `PbaAdmin`. Credentials are in `.env` only.
6. **Store config lives in PostgreSQL** (`iris_yolo_stores` table), not in a file. Add/update stores via SQL — no code change needed.
7. **YOLO model:** YOLOv8s (`yolov8s.pt`). Downloaded automatically on first run. CPU-only — no GPU on production server.
8. **Confidence threshold:** 0.35 (set in `.env` as `YOLO_CONFIDENCE_THRESHOLD`). Adjustable without code change.
9. **Idempotent by design:** Re-running the same store/date is safe — duplicates are skipped in S3 and upserted in DB.
10. **Only 1 store added so far** (`RRNAGAR BLR` → `iris/BLRRRN`). 129 more stores pending.
11. **Credentials must never be committed to GitHub.** `.env` is in `.gitignore`. `.env.example` is the template.

### Files to read first when resuming
1. `processor.py` — the core orchestration loop
2. `s3_io.py` — S3 operations and date folder detection
3. `db.py` — all DB interactions
4. `utils.py` — date parsing, filename parsing

### What is NOT done yet
- Remaining 129 stores not yet added to `iris_yolo_stores`
- Camera-to-floor mapping (`stores/camera_mapping.json`) not populated
- Linux server deployment not done
- Cron/scheduled automation not configured

---

## Module Registry

| Module | Purpose |
|--------|---------|
| `run.py` | CLI entry point — `--store` / `--date` / `--all-stores` |
| `config.py` | Loads `.env`, exposes all settings incl. AWS credentials |
| `db.py` | RDS PostgreSQL connection, store lookups, scan result upserts |
| `store_config.py` | Wraps db.py store queries |
| `s3_io.py` | S3 list / download / upload / exists / URL builder / date folder auto-detect |
| `yolo_detector.py` | YOLOv8s singleton — returns `(is_relevant, confidence, person_count)` |
| `processor.py` | Orchestrates one store/date run end-to-end |
| `utils.py` | Logger, `parse_any_date()`, `parse_filename()`, summary printer |
| `setup_db.sql` | DDL: `iris_yolo_stores` + `iris_yolo_scan_results` tables |
| `scripts/setup_db.py` | Creates DB tables via Python (no psql binary needed) |
| `scripts/validate_env.py` | Pre-flight check: env vars, RDS, AWS S3 |
| `scripts/run_store_scan.py` | Alternate CLI entry (delegates to `run.py`) |
| `scripts/backfill_store.py` | Reprocess a date range for a store |
| `stores/camera_mapping.json` | Camera-to-floor/zone mapping (future use) |
| `docs/OPERATIONS_RUNBOOK.md` | Full operator guide — all PS commands, troubleshooting, DB queries |

---

## Change Entries

### 2026-05-14 — v1.0 Complete: First successful end-to-end scan
**Changed paths:** All files created. Scripts: `scripts/setup_db.py`, `scripts/validate_env.py`. Docs: `docs/OPERATIONS_RUNBOOK.md`, updated `CHANGE_LEDGER.md`.

**What changed:**
- Full project scaffold created from scratch
- S3 input/output path convention locked in (same bucket, `relevant image/` subfolder)
- PostgreSQL RDS tables live: `iris_yolo_stores`, `iris_yolo_scan_results`
- YOLOv8s model downloaded and running on CPU
- Date format auto-detection implemented (`parse_any_date()` + `find_date_folder()`) — handles DD-MM-YY, YYYY-MM-DD, YYYYMMDD, and 7 other formats
- IAM user `iris-read-write-access` S3 permissions fixed (prefix-scoped policy)
- First real scan: RRNAGAR BLR / 2026-05-14 → 66 images, 52 relevant, 14 skipped, 0 failed
- S3 output confirmed: `s3://middle-ware/iris/BLRRRN/relevant image/14-05-26/`
- DB confirmed: 66 rows, 98 total persons detected

**AI handover note updated:** Yes

---
