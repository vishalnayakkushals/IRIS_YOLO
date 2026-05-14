"""Run DB setup directly via psycopg2 — no psql binary needed."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from db import get_connection

SQL = """
CREATE TABLE IF NOT EXISTS iris_yolo_stores (
    id             SERIAL       PRIMARY KEY,
    store_name     VARCHAR(100) NOT NULL UNIQUE,
    store_s3_code  VARCHAR(50)  NOT NULL,
    s3_bucket      VARCHAR(100) NOT NULL DEFAULT 'middle-ware',
    s3_prefix      VARCHAR(255) NOT NULL,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS iris_yolo_scan_results (
    id                SERIAL       PRIMARY KEY,
    store             VARCHAR(100) NOT NULL,
    date              DATE         NOT NULL,
    camera            VARCHAR(50)  NOT NULL,
    time              TIME         NOT NULL,
    image_name        VARCHAR(255) NOT NULL,
    drive_link        TEXT,
    yolo_person_count INTEGER      NOT NULL DEFAULT 0,
    yolo_confidence   FLOAT,
    review_status     VARCHAR(50)  NOT NULL DEFAULT 'pending',
    reviewer_comment  TEXT,
    processed_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_yolo_scan UNIQUE (store, date, image_name)
);

CREATE INDEX IF NOT EXISTS idx_yolo_scan_store_date
    ON iris_yolo_scan_results (store, date);
"""

INSERT_STORE = """
INSERT INTO iris_yolo_stores (store_name, store_s3_code, s3_bucket, s3_prefix)
VALUES ('RRNAGAR BLR', 'BLRRRN', 'middle-ware', 'iris/BLRRRN')
ON CONFLICT (store_name) DO NOTHING;
"""

def main():
    try:
        conn = get_connection()
        cur = conn.cursor()
        print("Connected to RDS iris-db.")

        cur.execute(SQL)
        conn.commit()
        print("[OK] Tables created: iris_yolo_stores, iris_yolo_scan_results")

        cur.execute(INSERT_STORE)
        conn.commit()
        print("[OK] Sample store 'RRNAGAR BLR' inserted (skipped if already exists).")

        # Verify
        cur.execute("SELECT store_name, s3_prefix FROM iris_yolo_stores WHERE is_active = TRUE;")
        rows = cur.fetchall()
        print(f"\nActive stores ({len(rows)}):")
        for r in rows:
            print(f"  {r[0]} -> {r[1]}")

        cur.close()
        conn.close()
        print("\nDB setup complete.")
    except Exception as e:
        print(f"[FAIL] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
