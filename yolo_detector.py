from ultralytics import YOLO
from config import YOLO_MODEL_PATH, YOLO_CONFIDENCE_THRESHOLD

_model = None
_PERSON_CLASS = 0


def get_model():
    global _model
    if _model is None:
        _model = YOLO(YOLO_MODEL_PATH)
    return _model


def is_relevant(image_path):
    """
    Returns (is_relevant: bool, max_confidence: float, person_count: int).
    Relevant = at least one person detected above confidence threshold.
    """
    model = get_model()
    results = model(
        image_path,
        verbose=False,
        conf=YOLO_CONFIDENCE_THRESHOLD,
        classes=[_PERSON_CLASS],
    )
    for result in results:
        count = len(result.boxes)
        if count > 0:
            confidences = result.boxes.conf.tolist()
            return True, max(confidences), count
    return False, 0.0, 0
