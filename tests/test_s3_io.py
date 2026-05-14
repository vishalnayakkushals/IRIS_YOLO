from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError


def test_key_exists_returns_true():
    with patch("s3_io.get_s3_client") as mock_fn:
        mock_client = MagicMock()
        mock_client.head_object.return_value = {}
        mock_fn.return_value = mock_client

        from s3_io import key_exists
        assert key_exists("test-bucket", "some/key.jpg") is True


def test_key_exists_returns_false_on_404():
    with patch("s3_io.get_s3_client") as mock_fn:
        mock_client = MagicMock()
        error = ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")
        mock_client.head_object.side_effect = error
        mock_fn.return_value = mock_client

        from s3_io import key_exists
        assert key_exists("test-bucket", "missing/key.jpg") is False


def test_list_images_filters_non_images():
    with patch("s3_io.get_s3_client") as mock_fn:
        mock_client = MagicMock()
        mock_pager = MagicMock()
        mock_client.get_paginator.return_value = mock_pager
        mock_pager.paginate.return_value = [{
            "Contents": [
                {"Key": "iris/BLRRRN/14-05-26/14-41-18_D13-1.jpg"},
                {"Key": "iris/BLRRRN/14-05-26/readme.txt"},
                {"Key": "iris/BLRRRN/14-05-26/thumb.png"},
            ]
        }]
        mock_fn.return_value = mock_client

        from s3_io import list_images
        keys = list_images("middle-ware", "iris/BLRRRN/14-05-26")
        assert len(keys) == 2
        assert all(k.endswith((".jpg", ".png")) for k in keys)
