"""
Bulk load all stores from stores/store_master.csv into iris_yolo_stores.
- Cleans all values (strip, handle '-' / '-' / 'N/A' as empty)
- Uses GoFrugal Name as store_name, Short code as store_s3_code
- S3 prefix = iris/<short_code>
- Skips rows with no short_code
- BLRRRN already exists — upserts safely (no duplicate)
- Prints full summary at end
"""
import sys, os, csv, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()
from db import get_connection

# Placeholder values from IRIS project pattern — treat as empty
_EMPTY_PLACEHOLDERS = {"-", "–", "—", "n/a", "na", "none", "null", "-,-", "--"}

def clean(value):
    """Strip whitespace. Treat placeholders as empty string."""
    v = str(value or "").strip()
    if v.lower() in _EMPTY_PLACEHOLDERS:
        return ""
    return v

def clean_email(value):
    return clean(value).lower()

def clean_code(value):
    """Short code — strip and uppercase."""
    return re.sub(r"[^A-Z0-9]", "", clean(value).upper())

# ALTER TABLE to add store master columns if not already present
ALTER_SQL = """
ALTER TABLE iris_yolo_stores
    ADD COLUMN IF NOT EXISTS gofrugal_name   VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS outlet_id       VARCHAR(50)  NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS city            VARCHAR(100) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS state           VARCHAR(100) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS zone            VARCHAR(50)  NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS country         VARCHAR(50)  NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS mobile_no       VARCHAR(20)  NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS store_email     VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS cluster_manager VARCHAR(100) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS area_manager    VARCHAR(100) NOT NULL DEFAULT '';
"""

UPSERT_SQL = """
INSERT INTO iris_yolo_stores
    (store_name, store_s3_code, s3_bucket, s3_prefix,
     gofrugal_name, outlet_id, city, state, zone, country,
     mobile_no, store_email, cluster_manager, area_manager,
     is_active, updated_at)
VALUES
    (%s, %s, 'middle-ware', %s,
     %s, %s, %s, %s, %s, %s,
     %s, %s, %s, %s,
     TRUE, NOW())
ON CONFLICT (store_name)
DO UPDATE SET
    store_s3_code    = EXCLUDED.store_s3_code,
    s3_prefix        = EXCLUDED.s3_prefix,
    gofrugal_name    = EXCLUDED.gofrugal_name,
    outlet_id        = EXCLUDED.outlet_id,
    city             = EXCLUDED.city,
    state            = EXCLUDED.state,
    zone             = EXCLUDED.zone,
    country          = EXCLUDED.country,
    mobile_no        = EXCLUDED.mobile_no,
    store_email      = EXCLUDED.store_email,
    cluster_manager  = EXCLUDED.cluster_manager,
    area_manager     = EXCLUDED.area_manager,
    is_active        = TRUE,
    updated_at       = NOW();
"""

def main():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "stores", "store_master.csv")
    if not os.path.exists(csv_path):
        print(f"[FAIL] CSV not found: {csv_path}")
        sys.exit(1)

    conn = get_connection()
    cur = conn.cursor()

    # Add new columns to existing table
    print("Migrating table schema...")
    cur.execute(ALTER_SQL)
    conn.commit()
    print("[OK] Schema updated.")

    # Read CSV
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    inserted, skipped, errors = 0, 0, []

    for row in rows:
        short_code  = clean_code(row.get("Short code", ""))
        gofrugal    = clean(row.get("GoFrugal Name", ""))
        outlet_id   = clean(row.get("Outlet id", ""))
        city        = clean(row.get("City", ""))
        state       = clean(row.get("State", ""))
        zone        = clean(row.get("Zone", ""))
        country     = clean(row.get("Country", ""))
        mobile      = clean(row.get("Mobile no.", ""))
        email       = clean_email(row.get("Store Email", ""))
        cluster_mgr = clean(row.get("Cluster Manager", ""))
        area_mgr    = clean(row.get("Area Manager", ""))

        # Skip rows with no short code or no name
        if not short_code or not gofrugal:
            skipped += 1
            continue

        store_name = gofrugal          # GoFrugal Name is the canonical store name
        s3_prefix  = f"iris/{short_code}"

        try:
            cur.execute(UPSERT_SQL, (
                store_name, short_code, s3_prefix,
                gofrugal, outlet_id, city, state, zone, country,
                mobile, email, cluster_mgr, area_mgr
            ))
            inserted += 1
        except Exception as e:
            errors.append(f"  Row {row.get('S.No','?')} ({short_code}): {e}")
            conn.rollback()

    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM iris_yolo_stores WHERE is_active = TRUE")
    total_active = cur.fetchone()[0]
    conn.close()

    print()
    print("=" * 50)
    print("  Store Master Bulk Load — Summary")
    print("=" * 50)
    print(f"  CSV rows read          : {len(rows)}")
    print(f"  Inserted / updated     : {inserted}")
    print(f"  Skipped (no code/name) : {skipped}")
    print(f"  Errors                 : {len(errors)}")
    print(f"  Total active in DB     : {total_active}")
    print("=" * 50)
    if errors:
        print("Errors:")
        for e in errors:
            print(e)

if __name__ == "__main__":
    main()
