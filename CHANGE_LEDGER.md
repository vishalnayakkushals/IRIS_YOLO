# IRIS_YOLO — Change Ledger

## Module Registry

| Module | Purpose |
|--------|---------|
| `run.py` | CLI entry point — `--store` / `--date` / `--all-stores` |
| `config.py` | Loads `.env`, exposes all settings incl. AWS credentials |
| `db.py` | RDS PostgreSQL connection, store lookups, scan result upserts |
| `store_config.py` | Wraps db.py store queries |
| `s3_io.py` | S3 list / download / upload / exists / URL builder |
| `yolo_detector.py` | YOLOv8s singleton — returns `(is_relevant, confidence, person_count)` |
| `processor.py` | Orchestrates one store/date run end-to-end |
| `utils.py` | Logger, `to_s3_date()`, `parse_filename()`, summary printer |
| `setup_db.sql` | DDL: `iris_yolo_stores` + `iris_yolo_scan_results` tables |
| `scripts/validate_env.py` | Pre-flight check: env vars, RDS, AWS S3 |
| `scripts/run_store_scan.py` | Alternate CLI entry (delegates to `run.py`) |
| `scripts/backfill_store.py` | Reprocess a date range for a store |
| `stores/camera_mapping.json` | Camera-to-floor/zone mapping (future use) |

---

## Change Entries

### 2026-05-14 — Initial scaffold + schema finalized
**Changed paths:** all files (initial creation)

- S3 input:  `s3://middle-ware/iris/<store_s3_code>/<DD-MM-YY>/<HH-MM-SS_CameraID.jpg>`
- S3 output: `s3://middle-ware/iris/<store_s3_code>/relevant image/<DD-MM-YY>/<filename.jpg>`
- Same bucket for input and output — output goes under `relevant image/` subfolder
- DB: RDS `iris-db`, tables `iris_yolo_stores` + `iris_yolo_scan_results`
- Table columns: Store, Date, Camera, Time, Image Name, Drive Link, YOLO Person Count, YOLO Confidence, Review Status, Reviewer Comment
- YOLO model: YOLOv8s, CPU-only, confidence threshold 0.35
- Filename parser extracts camera (`D13-1`) and time (`14:41:18`) from `14-41-18_D13-1.jpg`
- CLI date: `YYYY-MM-DD` → auto-converted to `DD-MM-YY` for S3 path
- Processing: sequential per image; `--all-stores` runs all active stores sequentially
- Idempotent: duplicate output key check before upload; upsert on DB conflict
