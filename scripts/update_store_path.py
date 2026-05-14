"""
Update the S3 prefix for a store.
Usage:
    python scripts/update_store_path.py --code BLRRRN --new-prefix iris/BLRRRN
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
import argparse
from db import get_connection


def main():
    parser = argparse.ArgumentParser(description="Update S3 prefix for a store")
    parser.add_argument("--code", required=True, help="Store short code (e.g. BLRRRN)")
    parser.add_argument("--new-prefix", required=True, help="New S3 prefix (e.g. iris/BLRRRN)")
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT store_s3_code, s3_prefix FROM iris_yolo_stores WHERE store_s3_code = %s",
        (args.code,)
    )
    row = cur.fetchone()
    if not row:
        print(f"[FAIL] Store '{args.code}' not found in DB.")
        conn.close()
        sys.exit(1)

    old_prefix = row[1]
    print(f"Store  : {args.code}")
    print(f"Old S3 : {old_prefix}")
    print(f"New S3 : {args.new_prefix}")
    confirm = input("Confirm update? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        conn.close()
        return

    cur.execute(
        "UPDATE iris_yolo_stores SET s3_prefix = %s, updated_at = NOW() WHERE store_s3_code = %s",
        (args.new_prefix, args.code)
    )
    conn.commit()
    print(f"[OK] Updated {cur.rowcount} row(s).")
    conn.close()


if __name__ == "__main__":
    main()
