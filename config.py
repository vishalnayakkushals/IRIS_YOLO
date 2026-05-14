import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "iris-db")
DB_USER = os.getenv("DB_USER", "PbaAdmin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "middle-ware")

YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8s.pt")
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.35"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
