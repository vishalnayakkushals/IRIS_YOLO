from unittest.mock import patch, MagicMock

STORE_DATA = {
    "store_name": "RRNAGAR BLR",
    "store_s3_code": "BLRRRN",
    "s3_bucket": "middle-ware",
    "s3_prefix": "iris/BLRRRN",
    "is_active": True,
}

IMAGE_KEY = "iris/BLRRRN/14-05-26/14-41-18_D13-1.jpg"
OUTPUT_KEY = "iris/BLRRRN/relevant image/14-05-26/14-41-18_D13-1.jpg"


def test_relevant_image_is_uploaded():
    with patch("processor.load_store", return_value=STORE_DATA), \
         patch("processor.list_images", return_value=[IMAGE_KEY]), \
         patch("processor.download_to_temp", return_value="/tmp/test.jpg"), \
         patch("processor.is_relevant", return_value=(True, 0.82, 2)), \
         patch("processor.key_exists", return_value=False), \
         patch("processor.upload_file") as mock_upload, \
         patch("processor.upsert_scan_result") as mock_upsert, \
         patch("os.path.exists", return_value=False):

        from processor import process_store_date
        stats = process_store_date("RRNAGAR BLR", "2026-05-14")

        assert stats["total"] == 1
        assert stats["relevant"] == 1
        assert stats["uploaded"] == 1
        assert stats["duplicate"] == 0
        assert stats["failed"] == 0
        mock_upload.assert_called_once()
        mock_upsert.assert_called_once()


def test_not_relevant_image_not_uploaded():
    with patch("processor.load_store", return_value=STORE_DATA), \
         patch("processor.list_images", return_value=[IMAGE_KEY]), \
         patch("processor.download_to_temp", return_value="/tmp/test.jpg"), \
         patch("processor.is_relevant", return_value=(False, 0.10, 0)), \
         patch("processor.upload_file") as mock_upload, \
         patch("processor.upsert_scan_result"), \
         patch("os.path.exists", return_value=False):

        from processor import process_store_date
        stats = process_store_date("RRNAGAR BLR", "2026-05-14")

        assert stats["not_relevant"] == 1
        assert stats["uploaded"] == 0
        mock_upload.assert_not_called()


def test_duplicate_skips_upload():
    with patch("processor.load_store", return_value=STORE_DATA), \
         patch("processor.list_images", return_value=[IMAGE_KEY]), \
         patch("processor.download_to_temp", return_value="/tmp/test.jpg"), \
         patch("processor.is_relevant", return_value=(True, 0.75, 1)), \
         patch("processor.key_exists", return_value=True), \
         patch("processor.upload_file") as mock_upload, \
         patch("processor.upsert_scan_result"), \
         patch("os.path.exists", return_value=False):

        from processor import process_store_date
        stats = process_store_date("RRNAGAR BLR", "2026-05-14")

        assert stats["duplicate"] == 1
        assert stats["uploaded"] == 0
        mock_upload.assert_not_called()
