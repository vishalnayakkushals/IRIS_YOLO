"""
Download output for a store+date — either relevant S3 images or DB scan results as CSV.

Usage:
    # Download relevant images from S3 to local folder
    python scripts/download_output.py --code BLRRRN --date 2026-05-14 --mode s3

    # Export DB scan results to CSV
    python scripts/download_output.py --code BLRRRN --date 2026-05-14 --mode csv

    # Both
    python scripts/download_output.py --code BLRRRN --date 2026-05-14 --mode both

Output folder: output/<code>/<date>/
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
import argparse
import boto3
from config import S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from db import get_connection, get_store

_RELEVANT_FOLDER = "relevant image"


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def download_s3_images(code, date_str, out_dir):
    store = get_store(code)
    if not store:
        print(f"[FAIL] Store '{code}' not found.")
        return

    s3_prefix = store["s3_prefix"]
    client = get_s3_client()

    # List relevant image folder
    prefix = f"{s3_prefix}/{_RELEVANT_FOLDER}/"
    paginator = client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)

    matched = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # Match by date token in path
            if date_str.replace("-", "") in key.replace("-", "").replace("/", "") or date_str in key:
                matched.append(key)

    if not matched:
        # Try flexible: list all subfolders and find one that contains the date digits
        date_digits = date_str.replace("-", "")
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                folder_part = key.replace(prefix, "").split("/")[0].replace("-", "")
                if date_digits[2:] in folder_part or date_digits in folder_part:
                    matched.append(key)

    if not matched:
        print(f"[INFO] No relevant images found in S3 for {code} on {date_str}")
        return

    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    print(f"Downloading {len(matched)} image(s) -> {img_dir}")
    for key in matched:
        filename = os.path.basename(key)
        dest = os.path.join(img_dir, filename)
        client.download_file(S3_BUCKET, key, dest)
        print(f"  Downloaded: {filename}")
    print(f"[OK] {len(matched)} image(s) saved to {img_dir}")


def export_db_csv(code, date_str, out_dir):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT store_code, date::text, camera, time::text, image_name,
               drive_link, yolo_person_count,
               ROUND(yolo_confidence::numeric, 4) AS yolo_confidence,
               review_status, reviewer_comment, processed_at::text
        FROM iris_yolo_scan_results
        WHERE store_code = %s AND date = %s
        ORDER BY time
    """, (code, date_str))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print(f"[INFO] No DB rows found for {code} on {date_str}")
        return

    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"scan_results_{code}_{date_str}.csv")
    headers = [
        "store_code", "date", "camera", "time", "image_name",
        "drive_link", "yolo_person_count", "yolo_confidence",
        "review_status", "reviewer_comment", "processed_at"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"[OK] {len(rows)} row(s) exported -> {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Download S3 images or DB CSV for a store+date")
    parser.add_argument("--code", required=True, help="Store short code (e.g. BLRRRN)")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--mode", choices=["s3", "csv", "both"], default="both",
                        help="What to download: s3=images, csv=DB export, both=all")
    args = parser.parse_args()

    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", args.code, args.date
    )

    if args.mode in ("s3", "both"):
        download_s3_images(args.code, args.date, out_dir)
    if args.mode in ("csv", "both"):
        export_db_csv(args.code, args.date, out_dir)


if __name__ == "__main__":
    main()
