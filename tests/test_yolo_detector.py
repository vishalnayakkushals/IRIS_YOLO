from unittest.mock import patch, MagicMock


def test_is_relevant_person_found():
    mock_box = MagicMock()
    mock_box.conf.tolist.return_value = [0.78, 0.65]

    mock_result = MagicMock()
    mock_result.boxes = [mock_box, mock_box]

    mock_model = MagicMock(return_value=[mock_result])

    with patch("yolo_detector.get_model", return_value=mock_model):
        from yolo_detector import is_relevant
        relevant, conf, count = is_relevant("dummy.jpg")
        assert relevant is True
        assert conf == 0.78
        assert count == 2


def test_is_relevant_no_person():
    mock_result = MagicMock()
    mock_result.boxes = []

    mock_model = MagicMock(return_value=[mock_result])

    with patch("yolo_detector.get_model", return_value=mock_model):
        from yolo_detector import is_relevant
        relevant, conf, count = is_relevant("dummy.jpg")
        assert relevant is False
        assert conf == 0.0
        assert count == 0
