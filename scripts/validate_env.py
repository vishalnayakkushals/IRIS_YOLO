import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

REQUIRED = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET"]

missing = [k for k in REQUIRED if not os.getenv(k)]
if missing:
    print(f"[FAIL] Missing env vars: {', '.join(missing)}")
    sys.exit(1)
print("[OK] All required env vars present.")

try:
    import psycopg2
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD, sslmode="require"
    )
    conn.close()
    print("[OK] PostgreSQL (RDS) connection successful.")
except Exception as e:
    print(f"[FAIL] PostgreSQL: {e}")
    sys.exit(1)

try:
    import boto3
    from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET
    s3 = boto3.client("s3", region_name=AWS_REGION,
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    # HeadBucket may be blocked by IAM prefix-scoped policy — use list instead
    s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="iris/", MaxKeys=1)
    print(f"[OK] AWS S3 reachable (bucket: {S3_BUCKET}, prefix: iris/).")
except Exception as e:
    print(f"[FAIL] AWS S3: {e}")
    sys.exit(1)

print("\nAll checks passed. Ready to run.")
