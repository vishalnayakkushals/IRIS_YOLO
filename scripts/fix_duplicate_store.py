import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from db import get_connection

conn = get_connection()
cur = conn.cursor()

# Show all BLRRRN entries
cur.execute("SELECT id, store_name, store_s3_code, city FROM iris_yolo_stores WHERE store_s3_code = 'BLRRRN' ORDER BY id")
print("BLRRRN entries before fix:")
for r in cur.fetchall():
    print(" ", r)

# Delete old manually-inserted entry (wrong canonical name)
cur.execute("DELETE FROM iris_yolo_stores WHERE store_name = 'RRNAGAR BLR'")
conn.commit()
print(f"Deleted old 'RRNAGAR BLR' entry: {cur.rowcount} row(s)")

# Update scan_results to match new canonical name from CSV
cur.execute("UPDATE iris_yolo_scan_results SET store = 'BLR - RR NAGAR' WHERE store = 'RRNAGAR BLR'")
conn.commit()
print(f"Updated scan_results store name: {cur.rowcount} row(s)")

# Final count
cur.execute("SELECT COUNT(*) FROM iris_yolo_stores WHERE is_active = TRUE")
print(f"Total active stores now: {cur.fetchone()[0]}")

# Verify BLRRRN
cur.execute("SELECT store_name, store_s3_code, s3_prefix, city FROM iris_yolo_stores WHERE store_s3_code = 'BLRRRN'")
print("BLRRRN after fix:", cur.fetchone())

conn.close()
