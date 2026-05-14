import os
import tempfile
import boto3
from botocore.exceptions import ClientError
from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY or None,
    )


def build_s3_url(bucket, key):
    from config import AWS_REGION
    return f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{key}"


def list_images(bucket, prefix):
    s3 = get_s3_client()
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(_IMAGE_EXTENSIONS):
                keys.append(key)
    return keys


def download_to_temp(bucket, key):
    s3 = get_s3_client()
    suffix = os.path.splitext(key)[1] or ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    s3.download_fileobj(bucket, key, tmp)
    tmp.close()
    return tmp.name


def key_exists(bucket, key):
    s3 = get_s3_client()
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def upload_file(local_path, bucket, key):
    s3 = get_s3_client()
    s3.upload_file(local_path, bucket, key)
