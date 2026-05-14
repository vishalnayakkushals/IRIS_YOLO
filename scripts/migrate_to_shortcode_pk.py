"""
Migration: Make store_s3_code the primary business key everywhere.
- iris_yolo_stores: adds UNIQUE constraint on store_s3_code
- iris_yolo_scan_results: renames 'store' column -> 'store_code', backfills short codes
- Recreates unique constraint and index using store_code
Safe to rerun — uses IF NOT EXISTS / IF EXISTS guards.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from db import get_connection

conn = get_connection()
cur = conn.cursor()

print("Step 1: Add UNIQUE constraint on store_s3_code...")
cur.execute("""
    DO $$ BEGIN
        ALTER TABLE iris_yolo_stores ADD CONSTRAINT uq_store_s3_code UNIQUE (store_s3_code);
    EXCEPTION WHEN duplicate_table THEN NULL;
    END $$;
""")
conn.commit()
print("  Done.")

print("Step 2: Rename 'store' column to 'store_code' in scan_results...")
cur.execute("""
    DO $$ BEGIN
        ALTER TABLE iris_yolo_scan_results RENAME COLUMN store TO store_code;
    EXCEPTION WHEN undefined_column THEN NULL;
    END $$;
""")
conn.commit()
print("  Done.")

print("Step 3: Backfill store_code with actual short codes...")
cur.execute("""
    UPDATE iris_yolo_scan_results sr
    SET store_code = s.store_s3_code
    FROM iris_yolo_stores s
    WHERE sr.store_code = s.store_name
      AND sr.store_code != s.store_s3_code;
""")
conn.commit()
print(f"  Updated {cur.rowcount} row(s).")

print("Step 4: Rebuild unique constraint using store_code...")
cur.execute("ALTER TABLE iris_yolo_scan_results DROP CONSTRAINT IF EXISTS uq_yolo_scan;")
cur.execute("""
    ALTER TABLE iris_yolo_scan_results
        ADD CONSTRAINT uq_yolo_scan UNIQUE (store_code, date, image_name);
""")
conn.commit()
print("  Done.")

print("Step 5: Rebuild index using store_code...")
cur.execute("DROP INDEX IF EXISTS idx_yolo_scan_store_date;")
cur.execute("""
    CREATE INDEX idx_yolo_scan_store_date
        ON iris_yolo_scan_results (store_code, date);
""")
conn.commit()
print("  Done.")

# Verify
cur.execute("SELECT store_code, date::text, COUNT(*) FROM iris_yolo_scan_results GROUP BY store_code, date")
rows = cur.fetchall()
print("\nVerification — scan_results by store_code/date:")
for r in rows:
    print(f"  store_code={r[0]}  date={r[1]}  rows={r[2]}")

cur.execute("SELECT COUNT(*) FROM iris_yolo_stores WHERE is_active = TRUE")
print(f"\nActive stores: {cur.fetchone()[0]}")
conn.close()
print("\nMigration complete.")
