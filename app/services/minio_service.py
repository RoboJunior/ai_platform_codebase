from minio import Minio
import json
from minio.error import S3Error

def create_minio_client(credentials: dict):
    minio_client = Minio(
    credentials['minio_server'],
    credentials['minio_access_key'],
    credentials['minio_secret_key'],
    secure=False 
    )
    return minio_client

# Create a bucket in minio
def create_bucket(bucket_name: str, credentails: dict):
    minio_client = create_minio_client(credentails)
    minio_client.make_bucket(bucket_name)

# Check bucket exists in minio
def check_bucket_exist(bucket_name: str, credentails: dict):
    minio_client = create_minio_client(credentails)
    return minio_client.bucket_exists(bucket_name)

# Delete bucket in minio
def delete_bucket(bucket_name: str, credentials: dict):
    minio_client = create_minio_client(credentials)
    return minio_client.remove_bucket(bucket_name)

# Get all the buckets
def list_all_buckets(credentials: dict):
    minio_client = create_minio_client(credentials)
    buckets = minio_client.list_buckets()
    return buckets
