import psycopg2
import psycopg2.extras
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        sslmode="require",
    )


def get_store(short_code):
    """Fetch store by store_s3_code (short code e.g. BLRRRN)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM iris_yolo_stores WHERE store_s3_code = %s AND is_active = TRUE",
                (short_code,)
            )
            return cur.fetchone()


def get_all_active_stores():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM iris_yolo_stores WHERE is_active = TRUE ORDER BY store_s3_code"
            )
            return cur.fetchall()


def upsert_scan_result(store_code, date, camera, time_str, image_name,
                       drive_link, yolo_person_count, yolo_confidence,
                       review_status="pending", reviewer_comment=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO iris_yolo_scan_results
                    (store_code, date, camera, time, image_name, drive_link,
                     yolo_person_count, yolo_confidence, review_status, reviewer_comment)
                VALUES (%s, %s, %s, %s::time, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ON CONSTRAINT uq_yolo_scan
                DO UPDATE SET
                    drive_link        = EXCLUDED.drive_link,
                    yolo_person_count = EXCLUDED.yolo_person_count,
                    yolo_confidence   = EXCLUDED.yolo_confidence,
                    review_status     = EXCLUDED.review_status,
                    reviewer_comment  = EXCLUDED.reviewer_comment,
                    processed_at      = NOW()
            """, (store_code, date, camera, time_str, image_name, drive_link,
                  yolo_person_count, yolo_confidence, review_status, reviewer_comment))
        conn.commit()
