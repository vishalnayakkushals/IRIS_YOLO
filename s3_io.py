import os
import tempfile
import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY or None,
    )


def build_s3_url(bucket: str, key: str) -> str:
    return f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{key}"


def list_date_folders(bucket: str, prefix: str) -> list[tuple[str, object]]:
    """
    List immediate subfolders under prefix that parse as a date.
    Returns [(folder_name, date_obj), ...] sorted newest first.
    Handles any date format (auto-detected via parse_any_date).
    """
    from utils import parse_any_date
    s3 = get_s3_client()
    clean_prefix = prefix.rstrip("/") + "/"
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=clean_prefix, Delimiter="/")
    results = []
    for cp in resp.get("CommonPrefixes", []):
        raw_prefix = cp["Prefix"].rstrip("/")
        folder_name = raw_prefix.split("/")[-1]
        parsed = parse_any_date(folder_name)
        if parsed is not None:
            results.append((folder_name, parsed))
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def find_date_folder(bucket: str, prefix: str, target_date_str: str) -> str | None:
    """
    Given a CLI date string (any format), find the matching folder name in S3.
    Returns the raw S3 folder name (e.g. '14-05-26') or None if not found.
    """
    from utils import parse_any_date
    target = parse_any_date(target_date_str)
    if target is None:
        raise ValueError(f"Cannot parse requested date: {target_date_str!r}")
    for folder_name, folder_date in list_date_folders(bucket, prefix):
        if folder_date == target:
            return folder_name
    return None


def list_images(bucket: str, prefix: str) -> list[str]:
    s3 = get_s3_client()
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(_IMAGE_EXTENSIONS):
                keys.append(key)
    return keys


def download_to_temp(bucket: str, key: str) -> str:
    s3 = get_s3_client()
    suffix = os.path.splitext(key)[1] or ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    s3.download_fileobj(bucket, key, tmp)
    tmp.close()
    return tmp.name


def key_exists(bucket: str, key: str) -> bool:
    s3 = get_s3_client()
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def upload_file(local_path: str, bucket: str, key: str) -> None:
    s3 = get_s3_client()
    s3.upload_file(local_path, bucket, key)
