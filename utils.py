import os
import re
import logging
from datetime import date, datetime
from typing import Optional
from config import LOG_LEVEL

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/iris_yolo_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)
logger = logging.getLogger("iris_yolo")

# ---------------------------------------------------------------------------
# Exhaustive date format detection (ported + extended from IRIS source_clients.py
# and yolo_relevance_scan.py). Handles every format seen in IRIS S3/Drive folders.
# ---------------------------------------------------------------------------
_DATE_TRYLIST = [
    # ISO: 2026-05-14
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
    # Compact ISO: 20260514
    (re.compile(r"^\d{8}$"), "%Y%m%d"),
    # DD-MM-YYYY: 14-05-2026
    (re.compile(r"^\d{2}-\d{2}-\d{4}$"), "%d-%m-%Y"),
    # DD-MM-YY: 14-05-26  ← current S3 format
    (re.compile(r"^\d{2}-\d{2}-\d{2}$"), "%d-%m-%y"),
    # DD/MM/YYYY: 14/05/2026
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "%d/%m/%Y"),
    # DD/MM/YY: 14/05/26
    (re.compile(r"^\d{2}/\d{2}/\d{2}$"), "%d/%m/%y"),
    # YYYY/MM/DD: 2026/05/14
    (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "%Y/%m/%d"),
    # YYYY_MM_DD: 2026_05_14
    (re.compile(r"^\d{4}_\d{2}_\d{2}$"), "%Y_%m_%d"),
    # DD_MM_YYYY: 14_05_2026
    (re.compile(r"^\d{2}_\d{2}_\d{4}$"), "%d_%m_%Y"),
    # DD_MM_YY: 14_05_26
    (re.compile(r"^\d{2}_\d{2}_\d{2}$"), "%d_%m_%y"),
    # MM-DD-YYYY: 05-14-2026 (US format, lower priority)
    (re.compile(r"^\d{2}-\d{2}-\d{4}$"), "%m-%d-%Y"),
]


def parse_any_date(token: str) -> Optional[date]:
    """Parse a folder/token string in any known date format. Returns None if unparseable."""
    text = str(token).strip()
    if not text:
        return None
    for pattern, fmt in _DATE_TRYLIST:
        if pattern.fullmatch(text):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    # dateutil fallback — handles edge cases and ambiguous formats
    try:
        from dateutil import parser as du_parser
        return du_parser.parse(text, dayfirst=True).date()
    except Exception:
        return None


def parse_filename(filename: str) -> tuple[str, str]:
    """
    Parse filename like '14-41-18_D13-1.jpg'
    Returns (time_str='14:41:18', camera='D13-1')
    Handles variations: HH-MM-SS_CameraID-Frame.jpg
    """
    name = os.path.splitext(filename)[0]
    parts = name.split("_", 1)
    if len(parts) == 2:
        time_raw, camera = parts[0], parts[1]
        time_str = time_raw.replace("-", ":")
        return time_str, camera
    return "00:00:00", name


def print_summary(store_name: str, date_str: str, stats: dict) -> None:
    print("\n" + "=" * 52)
    print("  IRIS YOLO — Scan Summary")
    print(f"  Store  : {store_name}")
    print(f"  Date   : {date_str}")
    print("=" * 52)
    print(f"  Total images scanned    : {stats['total']}")
    print(f"  Relevant images found   : {stats['relevant']}")
    print(f"  Non-relevant skipped    : {stats['not_relevant']}")
    print(f"  Uploaded to S3          : {stats['uploaded']}")
    print(f"  Duplicate / skipped     : {stats['duplicate']}")
    print(f"  Failed                  : {stats['failed']}")
    print(f"  DB rows inserted/updated: {stats['db_rows']}")
    print("=" * 52 + "\n")
