import os
from datetime import datetime
from utils import logger, parse_any_date, parse_filename, print_summary
from store_config import load_store
from s3_io import find_date_folder, list_images, download_to_temp, key_exists, upload_file, build_s3_url
from yolo_detector import is_relevant
from db import upsert_scan_result
from config import S3_BUCKET

_RELEVANT_FOLDER = "relevant image"


def _build_output_key(s3_prefix: str, date_folder: str, filename: str) -> str:
    return f"{s3_prefix}/{_RELEVANT_FOLDER}/{date_folder}/{filename}"


def process_store_date(store_name: str, date_str: str) -> dict:
    store = load_store(store_name)
    bucket = store.get("s3_bucket") or S3_BUCKET
    s3_prefix = store["s3_prefix"]

    # Auto-detect the S3 folder name regardless of date format
    date_folder = find_date_folder(bucket, s3_prefix, date_str)
    if date_folder is None:
        logger.warning(f"[{store_name}] No S3 folder found for date '{date_str}' under {s3_prefix}/")
        return {"total": 0, "relevant": 0, "not_relevant": 0,
                "uploaded": 0, "duplicate": 0, "failed": 0, "db_rows": 0}

    scan_date = parse_any_date(date_str)
    input_prefix = f"{s3_prefix}/{date_folder}"

    logger.info(f"[{store_name}] Matched folder '{date_folder}' for date '{date_str}'")
    logger.info(f"[{store_name}] Listing s3://{bucket}/{input_prefix}")
    image_keys = list_images(bucket, input_prefix)
    logger.info(f"[{store_name}] Found {len(image_keys)} images")

    stats = {
        "total": 0, "relevant": 0, "not_relevant": 0,
        "uploaded": 0, "duplicate": 0, "failed": 0, "db_rows": 0,
    }

    for key in image_keys:
        filename = os.path.basename(key)
        time_str, camera = parse_filename(filename)
        stats["total"] += 1
        tmp_path = None

        try:
            tmp_path = download_to_temp(bucket, key)
            relevant, confidence, person_count = is_relevant(tmp_path)

            output_key = _build_output_key(s3_prefix, date_folder, filename)
            drive_link = None

            if relevant:
                stats["relevant"] += 1
                if key_exists(bucket, output_key):
                    stats["duplicate"] += 1
                    drive_link = build_s3_url(bucket, output_key)
                    logger.debug(f"  Duplicate skip: {filename}")
                else:
                    upload_file(tmp_path, bucket, output_key)
                    drive_link = build_s3_url(bucket, output_key)
                    stats["uploaded"] += 1
                    logger.info(f"  Uploaded: {filename} (persons={person_count}, conf={confidence:.2f})")
            else:
                stats["not_relevant"] += 1
                logger.debug(f"  Not relevant: {filename} (conf={confidence:.2f})")

            upsert_scan_result(
                store=store_name,
                date=scan_date,
                camera=camera,
                time_str=time_str,
                image_name=filename,
                drive_link=drive_link,
                yolo_person_count=person_count,
                yolo_confidence=round(confidence, 4),
            )
            stats["db_rows"] += 1

        except Exception as e:
            stats["failed"] += 1
            logger.error(f"  FAILED: {filename} — {e}")
            upsert_scan_result(
                store=store_name,
                date=scan_date,
                camera=camera,
                time_str=time_str,
                image_name=filename,
                drive_link=None,
                yolo_person_count=0,
                yolo_confidence=0.0,
                review_status="error",
                reviewer_comment=str(e),
            )
            stats["db_rows"] += 1

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    print_summary(store_name, date_str, stats)
    return stats
