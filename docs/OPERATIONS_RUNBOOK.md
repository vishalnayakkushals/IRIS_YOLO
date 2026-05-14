# IRIS_YOLO — Operations Runbook
> Complete guide to run, manage, debug, and extend this project without Claude/Codex.
> All commands are PowerShell unless marked `[Linux]`.

---

## Table of Contents
1. [What This Project Does](#1-what-this-project-does)
2. [Project Map — What File Does What](#2-project-map)
3. [One-Time Setup](#3-one-time-setup)
4. [Daily Run Commands](#4-daily-run-commands)
5. [Store Management](#5-store-management)
6. [DB Queries — Check Results Without Code](#6-db-queries)
7. [S3 Operations — Check Output Without Code](#7-s3-operations)
8. [Troubleshooting — Problem → Cause → Fix](#8-troubleshooting)
9. [Confidence Tuning](#9-confidence-tuning)
10. [Linux Server Deployment](#10-linux-server-deployment)
11. [Cron Automation](#11-cron-automation)
12. [What You Can Do Without Claude](#12-self-service-operations)
13. [Pre-Deployment Checklist](#13-pre-deployment-checklist)

---

## 1. What This Project Does

```
S3 Input Folder          YOLO Detection         S3 Output Folder
iris/BLRRRN/             YOLOv8s                iris/BLRRRN/
  14-05-26/         →    Person present?    →     relevant image/
    img1.jpg              YES → upload              14-05-26/
    img2.jpg              NO  → skip                  img1.jpg
    img3.jpg                                         img3.jpg
                          + Save result to PostgreSQL for every image
```

**Input:** `s3://middle-ware/iris/<store_code>/<date_folder>/<HH-MM-SS_CameraID-Frame.jpg>`
**Output:** `s3://middle-ware/iris/<store_code>/relevant image/<date_folder>/<filename.jpg>`
**DB:** Table `iris_yolo_scan_results` in `iris-db` on AWS RDS

---

## 2. Project Map

```
IRIS_YOLO/
├── run.py                  ← START HERE — main CLI entry point
├── processor.py            ← core logic: S3 read → YOLO → S3 write → DB
├── yolo_detector.py        ← loads YOLOv8s model, detects persons
├── s3_io.py                ← all S3 operations (list/download/upload/check)
├── db.py                   ← all DB operations (connect/insert/upsert)
├── store_config.py         ← load store info from DB
├── utils.py                ← date parsing, filename parsing, logging
├── config.py               ← reads .env, exposes all settings
├── .env                    ← YOUR CREDENTIALS (never committed to git)
├── .env.example            ← template for .env
├── requirements.txt        ← pip packages
├── setup_db.sql            ← DB table definitions (reference)
├── scripts/
│   ├── setup_db.py         ← create DB tables (run once)
│   ├── validate_env.py     ← check all connections before running
│   ├── backfill_store.py   ← scan a date range for a store
│   ├── update_store_path.py ← change S3 prefix for a store
│   ├── download_output.py  ← download S3 images or export DB CSV
│   └── run_store_scan.py   ← alternate entry point
├── stores/
│   └── camera_mapping.json ← camera → floor/zone mapping (future)
├── logs/                   ← daily log files (auto-created)
└── docs/
    └── OPERATIONS_RUNBOOK.md ← this file
```

**Call chain:**
```
run.py → processor.py → s3_io.py        (list images, download, upload)
                      → yolo_detector.py (detect persons)
                      → db.py            (save results)
                      → utils.py         (parse dates, filenames, log)
```

---

## 3. One-Time Setup

### 3.1 Clone and create venv
```powershell
cd C:\Users\Kushals.DESKTOP-D51MT8S\Desktop\Github
git clone https://github.com/vishalnayakkushals/IRIS_YOLO.git
cd IRIS_YOLO
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3.2 Configure .env
```powershell
Copy-Item .env.example .env
notepad .env
```
Fill in your values (see `.env.example` for all keys). Never commit `.env` to git.

### 3.3 Create DB tables (run once)
```powershell
.\venv\Scripts\python.exe scripts/setup_db.py
```
Expected output:
```
Connected to RDS iris-db.
[OK] Tables created: iris_yolo_stores, iris_yolo_scan_results
[OK] Sample store 'RRNAGAR BLR' inserted
```

### 3.4 Validate all connections
```powershell
.\venv\Scripts\python.exe scripts/validate_env.py
```
Expected output:
```
[OK] All required env vars present.
[OK] PostgreSQL (RDS) connection successful.
[OK] AWS S3 reachable (bucket: middle-ware, prefix: iris/).
All checks passed. Ready to run.
```

---

## 4. Daily Run Commands

### Activate venv first (every new terminal session)
```powershell
cd C:\Users\Kushals.DESKTOP-D51MT8S\Desktop\Github\IRIS_YOLO
.\venv\Scripts\Activate.ps1
```

### Run one store for one date
```powershell
.\venv\Scripts\python.exe run.py --store BLRRRN --date "2026-05-14"
```
> `--store` now takes the **short code** (e.g. `BLRRRN`), not the store name.

### Run all active stores for one date
```powershell
.\venv\Scripts\python.exe run.py --all-stores --date "2026-05-14"
```

### Run all active stores for today
```powershell
$today = (Get-Date).ToString("yyyy-MM-dd")
.\venv\Scripts\python.exe run.py --all-stores --date $today
```

### Backfill a date range for one store
```powershell
.\venv\Scripts\python.exe scripts/backfill_store.py --store BLRRRN --from-date "2026-05-01" --to-date "2026-05-14"
```

### Check today's log
```powershell
$logfile = "logs/iris_yolo_" + (Get-Date).ToString("yyyyMMdd") + ".log"
Get-Content $logfile -Tail 50
```

### Re-run a store/date (safe — duplicates are skipped automatically)
```powershell
.\venv\Scripts\python.exe run.py --store "RRNAGAR BLR" --date "2026-05-14"
```

---

## 5. Store Management

All store operations are SQL. Run these via the Python one-liner below or any DB client (DBeaver, pgAdmin).

### Connect to DB (Python one-liner helper)
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from db import get_connection
conn = get_connection(); cur = conn.cursor()
# PASTE YOUR SQL HERE between the triple quotes
sql = '''SELECT store_name, s3_prefix, is_active FROM iris_yolo_stores ORDER BY store_name'''
cur.execute(sql); [print(r) for r in cur.fetchall()]
conn.close()
"
```

### List all active stores
```sql
SELECT store_name, store_s3_code, s3_prefix, is_active FROM iris_yolo_stores ORDER BY store_name;
```

### Add a new store
```sql
INSERT INTO iris_yolo_stores (store_name, store_s3_code, s3_bucket, s3_prefix)
VALUES ('GoFrugal Store Name', 'S3CODE', 'middle-ware', 'iris/S3CODE')
ON CONFLICT (store_name) DO NOTHING;
```
- `store_s3_code` = **primary key** — short code matching the S3 folder (e.g. `BLRRRN`). Use this in `--store` CLI arg.
- `store_name` = GoFrugal canonical name (human-readable, from store master CSV)
- `s3_prefix` = full S3 prefix path (e.g. `iris/BLRRRN`)

### Update a store's S3 path (interactive script)
```powershell
.\venv\Scripts\python.exe scripts/update_store_path.py --code BLRRRN --new-prefix iris/BLRRRN
```
This shows the old and new path and asks for confirmation before updating.

### Update a store's S3 path (direct SQL)
```sql
UPDATE iris_yolo_stores
SET s3_prefix = 'iris/NEWCODE', updated_at = NOW()
WHERE store_s3_code = 'S3CODE';
```

### Deactivate a store (exclude from --all-stores)
```sql
UPDATE iris_yolo_stores SET is_active = FALSE WHERE store_s3_code = 'S3CODE';
```

### Reactivate a store
```sql
UPDATE iris_yolo_stores SET is_active = TRUE WHERE store_s3_code = 'S3CODE';
```

### Bulk add stores (from a list)
Create a file `bulk_insert_stores.sql` with multiple INSERT statements, then run:
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from db import get_connection
conn = get_connection(); cur = conn.cursor()
with open('bulk_insert_stores.sql') as f: sql = f.read()
cur.execute(sql); conn.commit()
print('Done. Rows affected:', cur.rowcount)
conn.close()
"
```

---

## 6. DB Queries

Run any of these by pasting into the Python DB one-liner from Section 5.

### How many images scanned per store per date
```sql
SELECT store_code, date, COUNT(*) as total,
       SUM(CASE WHEN yolo_person_count > 0 THEN 1 ELSE 0 END) as relevant,
       SUM(CASE WHEN yolo_person_count = 0 THEN 1 ELSE 0 END) as not_relevant
FROM iris_yolo_scan_results
GROUP BY store_code, date
ORDER BY date DESC, store_code;
```

### Check results for a specific store and date
```sql
SELECT store_code, date, camera, time, image_name,
       yolo_person_count, round(yolo_confidence::numeric, 2),
       review_status, drive_link
FROM iris_yolo_scan_results
WHERE store_code = 'BLRRRN' AND date = '2026-05-14'
ORDER BY time;
```

### Find all failed images
```sql
SELECT store_code, date, image_name, reviewer_comment
FROM iris_yolo_scan_results
WHERE review_status = 'error'
ORDER BY processed_at DESC;
```

### Find all relevant images with drive links
```sql
SELECT store_code, date, camera, time, image_name, drive_link, yolo_person_count
FROM iris_yolo_scan_results
WHERE yolo_person_count > 0 AND drive_link IS NOT NULL
ORDER BY date DESC, store_code, time;
```

### Which dates have been scanned for a store
```sql
SELECT DISTINCT date, COUNT(*) as images
FROM iris_yolo_scan_results
WHERE store_code = 'BLRRRN'
GROUP BY date ORDER BY date DESC;
```

### Total persons detected per store (all time)
```sql
SELECT store_code, SUM(yolo_person_count) as total_persons,
       COUNT(*) as total_images,
       SUM(CASE WHEN yolo_person_count > 0 THEN 1 ELSE 0 END) as relevant_images
FROM iris_yolo_scan_results
GROUP BY store_code ORDER BY total_persons DESC;
```

### Delete scan results to reprocess a date (clean rerun)
```sql
DELETE FROM iris_yolo_scan_results
WHERE store_code = 'BLRRRN' AND date = '2026-05-14';
```
Then run the scan again — it will reprocess and re-upload everything.

### Export results to CSV (script — easiest way)
```powershell
.\venv\Scripts\python.exe scripts/download_output.py --code BLRRRN --date 2026-05-14 --mode csv
```
Output saved to `output/BLRRRN/2026-05-14/scan_results_BLRRRN_2026-05-14.csv`.

### Export results to CSV (Python one-liner)
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from db import get_connection
import csv, datetime
conn = get_connection(); cur = conn.cursor()
cur.execute('SELECT store_code, date, camera, time, image_name, drive_link, yolo_person_count, yolo_confidence, review_status, reviewer_comment FROM iris_yolo_scan_results ORDER BY date DESC, store_code, time')
rows = cur.fetchall()
cols = ['Store Code','Date','Camera','Time','Image Name','Drive Link','YOLO Person Count','YOLO Confidence','Review Status','Reviewer Comment']
fname = 'scan_results_' + datetime.date.today().strftime('%Y%m%d') + '.csv'
with open(fname,'w',newline='') as f:
    w = csv.writer(f); w.writerow(cols); w.writerows(rows)
print('Exported', len(rows), 'rows to', fname)
conn.close()
"
```

---

## 7. S3 Operations

### List date folders available for a store
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from s3_io import list_date_folders
folders = list_date_folders('middle-ware', 'iris/BLRRRN')
for name, dt in folders: print(name, '->', dt)
"
```

### Count images in a store/date folder
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from s3_io import list_images
keys = list_images('middle-ware', 'iris/BLRRRN/14-05-26')
print('Total images:', len(keys))
"
```

### Count relevant images already uploaded (output folder)
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from s3_io import list_images
keys = list_images('middle-ware', 'iris/BLRRRN/relevant image/14-05-26')
print('Relevant images in S3:', len(keys))
for k in keys[:5]: print(' ', k)
"
```

### Verify a specific output image exists
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from s3_io import key_exists
key = 'iris/BLRRRN/relevant image/14-05-26/14-41-18_D13-1.jpg'
print('Exists:', key_exists('middle-ware', key))
"
```

---

## 8. Troubleshooting

### Problem: `[FAIL] PostgreSQL connection failed`
**Cause:** Wrong DB credentials or RDS not reachable.
**Fix:**
1. Check `.env` — `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
2. Check your internet/VPN — RDS is on AWS
3. Check RDS security group allows inbound port 5432 from your IP
```powershell
# Test connection only
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
import psycopg2, os
try:
    conn = psycopg2.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'), sslmode='require', connect_timeout=5)
    print('Connected OK'); conn.close()
except Exception as e: print('FAIL:', e)
"
```

### Problem: `[FAIL] AWS S3: AccessDenied`
**Cause:** IAM user missing S3 permissions.
**Fix:** In AWS IAM Console → user `iris-read-write-access` → add inline policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["s3:ListBucket"],
     "Resource": "arn:aws:s3:::middle-ware",
     "Condition": {"StringLike": {"s3:prefix": ["iris/*"]}}},
    {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject", "s3:HeadObject"],
     "Resource": "arn:aws:s3:::middle-ware/iris/*"}
  ]
}
```

### Problem: `No S3 folder found for date 'YYYY-MM-DD'`
**Cause:** The date folder doesn't exist in S3 for that store, or date was typed wrong.
**Fix:** List what folders actually exist for the store:
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from s3_io import list_date_folders
for name, dt in list_date_folders('middle-ware', 'iris/BLRRRN'): print(name, dt)
"
```
Use one of the listed dates in your `--date` argument.

### Problem: `Store 'X' not found or inactive`
**Cause:** Short code not in `iris_yolo_stores` table or `is_active = FALSE`. The `--store` arg now takes the **short code** (e.g. `BLRRRN`), not the store name.
**Fix:**
```sql
-- Check if store exists by short code
SELECT store_s3_code, store_name, is_active FROM iris_yolo_stores WHERE store_s3_code = 'X';
-- If missing, add it:
INSERT INTO iris_yolo_stores (store_name, store_s3_code, s3_bucket, s3_prefix)
VALUES ('GoFrugal Name', 'X', 'middle-ware', 'iris/X');
-- If inactive, reactivate:
UPDATE iris_yolo_stores SET is_active = TRUE WHERE store_s3_code = 'X';
```

### Problem: `Found 0 images` for a known folder
**Cause:** Prefix is wrong or images have non-standard extensions.
**Fix:** Check what's actually in S3:
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from s3_io import get_s3_client
s3 = get_s3_client()
r = s3.list_objects_v2(Bucket='middle-ware', Prefix='iris/BLRRRN/14-05-26/', MaxKeys=10)
for o in r.get('Contents', []): print(o['Key'])
"
```
If you see `.JPG` (uppercase) — the extension filter in `s3_io.py` uses `.lower()` so it handles this.
If there are no objects, the prefix is wrong — check the store's `s3_prefix` in the DB.

### Problem: Too many images marked `not_relevant` (low confidence)
**Cause:** Confidence threshold too high for the camera quality.
**Fix:** Lower the threshold in `.env`:
```
YOLO_CONFIDENCE_THRESHOLD=0.25
```
Then rerun. See Section 9 for tuning guidance.

### Problem: `YOLO model not found / download fails`
**Cause:** `yolov8s.pt` file missing and no internet to download.
**Fix:** On a machine with internet, run once:
```powershell
.\venv\Scripts\python.exe -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
```
Then copy `yolov8s.pt` to the server manually. Set `YOLO_MODEL_PATH=yolov8s.pt` in `.env`.

### Problem: Images uploaded but drive_link is NULL in DB
**Cause:** Bug in a previous version. Fixed in current version.
**Fix:** Delete the affected rows and rerun:
```sql
DELETE FROM iris_yolo_scan_results WHERE store_code = 'SCODE' AND date = 'YYYY-MM-DD';
```
Then rerun. The upsert will refill the rows with correct `drive_link`.

### Problem: Duplicate images being uploaded
**Cause:** Should not happen — `key_exists()` check prevents this.
**Check:** If you suspect duplicates, compare S3 object count vs DB `uploaded` count:
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from s3_io import list_images
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute(\"SELECT COUNT(*) FROM iris_yolo_scan_results WHERE store_code='BLRRRN' AND date='2026-05-14' AND yolo_person_count > 0\")
db_count = cur.fetchone()[0]
s3_count = len(list_images('middle-ware', 'iris/BLRRRN/relevant image/14-05-26'))
print('DB relevant:', db_count, '| S3 output files:', s3_count)
conn.close()
"
```

### Problem: `ModuleNotFoundError` when running scripts
**Cause:** venv not activated.
**Fix:**
```powershell
.\venv\Scripts\Activate.ps1
# OR run with full venv path:
.\venv\Scripts\python.exe run.py --store "X" --date "2026-05-14"
```

---

## 9. Confidence Tuning

The confidence threshold controls how strict YOLO is. Default: `0.35`

| Threshold | Behaviour | Use when |
|-----------|-----------|----------|
| 0.20 | Very permissive — captures partial/blurry people. More false positives | Camera quality is poor |
| 0.35 | Balanced (current default) | Normal retail cameras |
| 0.50 | Strict — only clear, full-body detections | High-res cameras, reduce false positives |

**To change:** Edit `.env`:
```
YOLO_CONFIDENCE_THRESHOLD=0.25
```
No code change needed. Restart the script.

**To test one image manually:**
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from s3_io import download_to_temp
from yolo_detector import is_relevant
tmp = download_to_temp('middle-ware', 'iris/BLRRRN/14-05-26/14-41-18_D13-1.jpg')
relevant, conf, count = is_relevant(tmp)
print('Relevant:', relevant, '| Confidence:', round(conf,3), '| Person count:', count)
"
```

---

## 10. Linux Server Deployment

```bash
# 1. Clone
git clone https://github.com/vishalnayakkushals/IRIS_YOLO.git
cd IRIS_YOLO

# 2. Setup venv
python3 -m venv venv
source venv/bin/activate

# 3. Install
pip install -r requirements.txt

# 4. Configure .env (create manually — do NOT scp .env from Windows)
cp .env.example .env
nano .env
# Fill in DB credentials, AWS keys, S3 bucket, YOLO path

# 5. Create DB tables (only if not already done)
python scripts/setup_db.py

# 6. Validate
python scripts/validate_env.py

# 7. Run first scan
python run.py --store BLRRRN --date "$(date +%Y-%m-%d)"
```

### Linux: check logs
```bash
tail -f logs/iris_yolo_$(date +%Y%m%d).log
```

### Linux: run all stores for today
```bash
python run.py --all-stores --date "$(date +%Y-%m-%d)"
```

---

## 11. Cron Automation

### Linux cron — run all stores daily at 11 PM
```bash
crontab -e
```
Add this line:
```
0 23 * * * cd /home/ubuntu/IRIS_YOLO && ./venv/bin/python run.py --all-stores --date $(date +\%Y-\%m-\%d) >> logs/cron.log 2>&1
```

### Linux cron — run a specific store daily
```
0 23 * * * cd /home/ubuntu/IRIS_YOLO && ./venv/bin/python run.py --store BLRRRN --date $(date +\%Y-\%m-\%d) >> logs/cron.log 2>&1
```

### Check cron is running
```bash
grep CRON /var/log/syslog | tail -20
cat logs/cron.log | tail -50
```

---

## 12. Self-Service Operations

> Everything in this section can be done without Claude or any AI.

### Add a new store (no code change)
1. Get the short code and GoFrugal name (e.g. `BLRRRN` from `iris/BLRRRN/`)
2. Run this:
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute('''INSERT INTO iris_yolo_stores (store_name, store_s3_code, s3_bucket, s3_prefix)
               VALUES (%s, %s, 'middle-ware', %s) ON CONFLICT (store_name) DO NOTHING''',
            ('GoFrugal Store Name', 'S3CODE', 'iris/S3CODE'))
conn.commit(); print('Done'); conn.close()
"
```
Then run with: `.\venv\Scripts\python.exe run.py --store S3CODE --date 2026-05-14`

### Update a store's S3 path (interactive)
```powershell
.\venv\Scripts\python.exe scripts/update_store_path.py --code BLRRRN --new-prefix iris/BLRRRN
```

### Download S3 output images locally
```powershell
.\venv\Scripts\python.exe scripts/download_output.py --code BLRRRN --date 2026-05-14 --mode s3
```
Images saved to `output/BLRRRN/2026-05-14/images/`

### Export DB results as CSV
```powershell
.\venv\Scripts\python.exe scripts/download_output.py --code BLRRRN --date 2026-05-14 --mode csv
```
CSV saved to `output/BLRRRN/2026-05-14/scan_results_BLRRRN_2026-05-14.csv`

### Change confidence threshold
Edit `.env` → change `YOLO_CONFIDENCE_THRESHOLD=0.25`. Re-run. Done.

### Check if a scan already ran for a date
```powershell
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM iris_yolo_scan_results WHERE store_code=%s AND date=%s',
            ('BLRRRN','2026-05-14'))
print('Rows in DB:', cur.fetchone()[0]); conn.close()
"
```

### Export full results to CSV (no DB client needed)
See Section 6 — CSV export command. Run it, open the CSV in Excel.

### Reprocess a failed date
```powershell
# Step 1: Delete old results
.\venv\Scripts\python.exe -c "
from dotenv import load_dotenv; load_dotenv()
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute('DELETE FROM iris_yolo_scan_results WHERE store_code=%s AND date=%s',
            ('BLRRRN','2026-05-14'))
conn.commit(); print('Deleted', cur.rowcount, 'rows'); conn.close()
"
# Step 2: Re-run scan
.\venv\Scripts\python.exe run.py --store BLRRRN --date "2026-05-14"
```

### Update .env without breaking anything
`.env` is read fresh every time you run a command. Just edit it and re-run. No restart needed.

### Pull latest code from GitHub (when updates are pushed)
```powershell
cd C:\Users\Kushals.DESKTOP-D51MT8S\Desktop\Github\IRIS_YOLO
git pull origin main
# No rebuild needed — just rerun
```

### What to do if a run crashes mid-way
Just re-run the same command. It is fully idempotent:
- Images already uploaded to S3 will be skipped (duplicate check)
- DB rows already written will be upserted (no duplicates)
- Images not yet processed will be processed fresh

```powershell
.\venv\Scripts\python.exe run.py --store BLRRRN --date "2026-05-14"
```

---

---

## 13. Pre-Deployment Checklist

---

### A. Before You Leave Your Machine (Windows)

- [ ] All code changes pushed to GitHub (`git push origin main`)
- [ ] `.env` file is **NOT** in GitHub (run `git status` — it must not appear)
- [ ] `output/` folder not in GitHub (gitignored)
- [ ] Note down all `.env` values — you will need to re-enter them on the server

---

### B. Server — Minimum Requirements

- [ ] Linux server available (Ubuntu 20.04+ recommended)
- [ ] At least **2 GB free disk** (PyTorch alone is ~750 MB)
- [ ] At least **2 GB RAM**
- [ ] Python 3.9 or higher installed (`python3 --version`)
- [ ] Internet access on server (to clone GitHub and download packages)
- [ ] Port 5432 outbound open (to reach AWS RDS)

---

### C. Server — Setup Steps

```bash
git clone https://github.com/vishalnayakkushals/IRIS_YOLO.git
cd IRIS_YOLO
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt        # takes 5-10 min
cp .env.example .env && nano .env      # fill in all values
```

- [ ] Repo cloned
- [ ] venv created and activated
- [ ] `pip install -r requirements.txt` completed with no errors
- [ ] `.env` created and all values filled in:
  - [ ] `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
  - [ ] `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
  - [ ] `S3_BUCKET=middle-ware`
  - [ ] `YOLO_MODEL_PATH=yolov8s.pt`
  - [ ] `YOLO_CONFIDENCE_THRESHOLD=0.35`

---

### D. Server — Verify Before First Run

```bash
python scripts/validate_env.py
```

- [ ] `[OK] All required env vars present`
- [ ] `[OK] PostgreSQL (RDS) connection successful`
- [ ] `[OK] AWS S3 reachable`
- [ ] YOLO model downloaded: `ls -lh yolov8s.pt` shows ~22 MB
- [ ] DB has stores: `python scripts/check_db.py` shows `iris_yolo_stores: 133 rows`

---

### E. Server — First Test Run

```bash
python run.py --store BLRRRN --date 2026-05-14
```

- [ ] Output shows images found (not 0)
- [ ] Output shows relevant images uploaded to S3
- [ ] No errors in terminal output
- [ ] DB has rows: `python scripts/check_db.py`
- [ ] Log file created: `ls logs/`

---

### F. Production Ready

- [ ] First test run passed with no errors
- [ ] Cron job set up for daily automation (see Section 11)
- [ ] `logs/` folder is being written to after each run
- [ ] Team knows the log path for monitoring

---

*Last updated: 2026-05-14 | Maintained by: IRIS_YOLO project*
