import os
import logging
from datetime import datetime
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


def to_s3_date(date_str):
    """YYYY-MM-DD → DD-MM-YY (S3 folder format used by source images)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%d-%m-%y")


def parse_filename(filename):
    """
    Parse filename like '14-41-18_D13-1.jpg'
    Returns (time_str='14:41:18', camera='D13-1')
    """
    name = os.path.splitext(filename)[0]
    parts = name.split("_", 1)
    if len(parts) == 2:
        time_raw, camera = parts[0], parts[1]
        time_str = time_raw.replace("-", ":")
        return time_str, camera
    return "00:00:00", name


def print_summary(store_name, date_str, stats):
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
