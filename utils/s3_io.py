# utils/s3_io.py
# ──────────────────────────────────────────────────────────────
# MODULE: s3_io.py
# PURPOSE: S3 integration for PowerPlay data persistence.
# ──────────────────────────────────────────────────────────────

"""
Module: s3_io.py
Description:
    Provides simple upload, download, and list utilities for AWS S3.
    Used by PowerPlay scripts to store draws, analyses, and plots.
"""

import boto3
from botocore.exceptions import ClientError

# default region for local/dev use
DEFAULT_REGION = "us-east-1"


def get_s3_client(profile_name=None, region_name=DEFAULT_REGION):
    """
    Create and return a boto3 S3 client.

    Args:
        profile_name (str | None): Optional AWS CLI profile to use.
        region_name (str): AWS region to connect to.
    """
    if profile_name:
        session = boto3.Session(profile_name=profile_name, region_name=region_name)
        return session.client("s3")
    # fallback to whatever is in ~/.aws/credentials, but force region
    return boto3.client("s3", region_name=region_name)


def upload_file(local_path, bucket, key, profile_name=None):
    """Upload a local file to S3."""
    s3 = get_s3_client(profile_name=profile_name)
    try:
        s3.upload_file(local_path, bucket, key)
        print(f"✅ Uploaded {local_path} → s3://{bucket}/{key}")
    except ClientError as exc:
        print(f"❌ Upload failed: {exc}")


def download_file(bucket, key, local_path, profile_name=None):
    """Download a file from S3 to a local path."""
    s3 = get_s3_client(profile_name=profile_name)
    try:
        s3.download_file(bucket, key, local_path)
        print(f"✅ Downloaded s3://{bucket}/{key} → {local_path}")
    except ClientError as exc:
        print(f"❌ Download failed: {exc}")


def list_files(bucket, prefix="", profile_name=None):
    """List files in an S3 bucket (optionally under a prefix)."""
    s3 = get_s3_client(profile_name=profile_name)
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" not in resp:
            print("📭 No files found.")
            return []
        keys = [obj["Key"] for obj in resp["Contents"]]
        for k in keys:
            print(f"🪣 {k}")
        return keys
    except ClientError as exc:
        print(f"❌ List failed: {exc}")
        return []
