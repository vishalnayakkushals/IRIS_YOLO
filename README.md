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
psql -h <host> -U <user> -d iris-db -f setup_db.sql

# 5. Add a store
psql -h <host> -U PbaAdmin -d iris-db -c "
INSERT INTO iris_yolo_stores (store_name, store_s3_code, s3_bucket, s3_prefix)
VALUES ('RRNAGAR BLR', 'BLRRRN', 'middle-ware', 'iris/BLRRRN');"

# 6. Validate
python scripts/validate_env.py

# 7. Run
python run.py --store "RRNAGAR BLR" --date "2026-05-14"
```

## S3 Path Convention

| | Format | Example |
|---|---|---|
| Input | `s3://middle-ware/iris/<store_s3_code>/<date_folder>/<filename>.jpg` | `s3://middle-ware/iris/BLRRRN/14-05-26/14-41-18_D13-1.jpg` |
| Output | `s3://middle-ware/iris/<store_s3_code>/relevant image/<date_folder>/<filename>.jpg` | `s3://middle-ware/iris/BLRRRN/relevant image/14-05-26/14-41-18_D13-1.jpg` |

Date folder format is auto-detected (any format supported).

## Tests

```bash
pytest tests/
```
