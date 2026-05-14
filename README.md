# IRIS_YOLO

Standalone YOLO relevance detection pipeline for retail store images.

**Flow:** S3 input → YOLOv8s → S3 output (relevant only) + PostgreSQL metadata

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/vishalnayakkushals/IRIS_YOLO.git
cd IRIS_YOLO
python -m venv venv
source venv/bin/activate        # Linux
# venv\Scripts\Activate.ps1    # Windows PowerShell

# 2. Install deps
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your DB + S3 settings

# 4. Setup DB (run once)
psql -U <user> -d <dbname> -f setup_db.sql

# 5. Add a store to DB (example)
psql -U <user> -d <dbname> -c "
INSERT INTO stores (store_name, store_s3_code, s3_input_prefix, s3_output_bucket, s3_output_prefix)
VALUES ('RRNAGAR BLR', 'BLRRRN', 'iris/BLRRRN', 'middle-ware-output', 'RRNAGAR BLR');"

# 6. Validate setup
python scripts/validate_env.py

# 7. Run a store scan
python run.py --store "RRNAGAR BLR" --date "2026-05-14"

# 8. Run all active stores
python run.py --all-stores --date "2026-05-14"

# 9. Backfill a date range
python scripts/backfill_store.py --store "RRNAGAR BLR" --from-date "2026-05-01" --to-date "2026-05-14"
```

## S3 Path Convention

| | Format | Example |
|---|---|---|
| Input | `s3://<input_bucket>/iris/<store_s3_code>/<DD-MM-YY>/<filename>.jpg` | `s3://middle-ware/iris/BLRRRN/14-05-26/14-41-18_D13-1.jpg` |
| Output | `s3://<output_bucket>/<store_name>/Relevant image/<DD-MM-YY>/<filename>.jpg` | `s3://middle-ware-output/RRNAGAR BLR/Relevant image/14-05-26/14-41-18_D13-1.jpg` |

## Tests

```bash
pytest tests/
```
