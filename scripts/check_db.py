import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from db import get_connection

conn = get_connection()
cur = conn.cursor()

# All tables in the schema
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
print("=== Tables in iris-db (public schema) ===")
for t in tables:
    print(" ", t)

# Row counts
print()
print("=== Row counts ===")
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {cur.fetchone()[0]} rows")

# Sample scan results
print()
print("=== iris_yolo_scan_results (last 5 rows) ===")
cur.execute("""
    SELECT store_code, date::text, camera, time::text, image_name,
           yolo_person_count, round(yolo_confidence::numeric,2), review_status
    FROM iris_yolo_scan_results
    ORDER BY processed_at DESC LIMIT 5
""")
for r in cur.fetchall():
    print(" ", r)

# Sample stores
print()
print("=== iris_yolo_stores ===")
cur.execute("SELECT store_name, s3_prefix, is_active FROM iris_yolo_stores")
for r in cur.fetchall():
    print(" ", r)

conn.close()
