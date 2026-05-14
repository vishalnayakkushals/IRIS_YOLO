-- IRIS YOLO — one-time DB setup
-- Target DB: iris-db on RDS
-- Run: psql -h pba-rds.cpca96t4u31g.ap-south-1.rds.amazonaws.com -U PbaAdmin -d iris-db -f setup_db.sql

-- Store registry
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

-- YOLO scan results
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

-- ---------------------------------------------------------------
-- Add a store (run per store — update values as needed)
-- ---------------------------------------------------------------
-- s3_prefix is the input prefix. Output = s3_prefix/relevant image/<date>/<file>
--
-- INSERT INTO iris_yolo_stores (store_name, store_s3_code, s3_bucket, s3_prefix)
-- VALUES ('RRNAGAR BLR', 'BLRRRN', 'middle-ware', 'iris/BLRRRN');

-- Update a store:
-- UPDATE iris_yolo_stores SET s3_prefix = 'iris/NEW_CODE', updated_at = NOW()
--     WHERE store_name = 'RRNAGAR BLR';

-- Deactivate a store:
-- UPDATE iris_yolo_stores SET is_active = FALSE WHERE store_name = 'RRNAGAR BLR';
