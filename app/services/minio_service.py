from minio import Minio
import json
from minio.error import S3Error
from app.core.config import get_settings
from temporalio.client import Client
from temporalio.common import SearchAttributeKey, SearchAttributePair, TypedSearchAttributes
from fastapi import HTTPException
from app.services.vault_service import get_secret
from app.workers.temporal.workflows.create_bucket_workflow import BucketCreationWorkFlow
from app.services.notification_service import start_app_notifications_workflow
import uuid
from sqlalchemy.orm import Session

def create_minio_client(credentials: dict):
    minio_client = Minio(
    credentials['minio_server'],
    credentials['minio_access_key'],
    credentials['minio_secret_key'],
    secure=False 
    )
    return minio_client

# Create a bucket in minio
async def create_minio_bucket(team_id: int, bucket_name: str, credentails: dict, db: Session):
    minio_client = create_minio_client(credentails)
    minio_client.make_bucket(bucket_name)
    await start_app_notifications_workflow([{"team_id": team_id}], f"New bucket added to the team with name {bucket_name}", db)

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

# Create a temporal client
async def create_temporal_client():
    return await Client.connect(get_settings().TEMPORAL_URL)

async def get_workflow_handle(client: Client, workflow_id: str):
    return client.get_workflow_handle(workflow_id)

# Create bucket request using temporlio
async def create_bucket_request_temporilio(user_id: int, team_id: int, bucket_name: str, team_name: str):
    user_id_key = SearchAttributeKey.for_int("UserId")
    bucket_name_key = SearchAttributeKey.for_keyword("BucketName")
    team_id_key = SearchAttributeKey.for_int("TeamId")

    client = await create_temporal_client()

    task_id = uuid.uuid4().hex

    handle = await client.start_workflow(
        BucketCreationWorkFlow.create_new_bucket,
        args=[bucket_name, team_name, team_id],
        id=f"bucket-{task_id}",
        task_queue="bucket-creation-task-queue",
        search_attributes=TypedSearchAttributes([
            SearchAttributePair(user_id_key, user_id),
            SearchAttributePair(bucket_name_key, bucket_name),
            SearchAttributePair(team_id_key, team_id)
        ])
    )
    return handle.id

# # Create Bucket temporilio activity
# async def create_bucket_temporilio_activity(team_name: str, bucket_name: str):
#     # Get the secret credentials from the vault
#     credentails = get_secret(f"{team_name}/minio_credentials")

#     # If the bucket exist raise a http exception
#     if check_bucket_exist(bucket_name, json.loads(credentails)):
#         raise HTTPException(status_code=403, detail="Bucket already exits!")
    
#     # create a new bucket 
#     create_bucket(bucket_name, json.loads(credentails))

#     return f"Bucket {bucket_name} created successfully!"

async def list_all_buckets_request_team(team_id: int):
    pending_requests = []

    client = await create_temporal_client()

    async for workflow in client.list_workflows(f'TeamId="{team_id}" and ExecutionStatus = "Running"'):
        pending_requests.append({
            "workflow_id": workflow.id,
            "run_id": workflow.run_id,
            "status": workflow.status.name,  # Should be RUNNING for pending workflows
            "start_time": workflow.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "bucket_name": workflow.search_attributes.get("BucketName", ["Unknown"])[0]
        })

    return {"pending_requests": pending_requests}

async def list_all_buckets_request_user(user_id: int, team_id: int):
    pending_requests = []

    client = await create_temporal_client()

    async for workflow in client.list_workflows(f'TeamId="{team_id}" and UserId="{user_id}" and ExecutionStatus = "Running"'):
        pending_requests.append({
            "workflow_id": workflow.id,
            "run_id": workflow.run_id,
            "status": workflow.status.name,  # Should be RUNNING for pending workflows
            "start_time": workflow.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "bucket_name": workflow.search_attributes.get("BucketName", ["Unknown"])[0]
        })

    return {"pending_requests": pending_requests}

# Approve bucket creation request
async def approve_create_bucket(workflow_id: str):
    client = await create_temporal_client()

    handle = await get_workflow_handle(client, workflow_id)

    workflow_info = await handle.describe()

    user_id = workflow_info.search_attributes.get('UserId', [None])[0]
    bucket_name = workflow_info.search_attributes.get('BucketName', [None])[0]

    if workflow_info.status == 2:
        raise HTTPException(status_code=404, detail='Workflow already completed!')

    # Send approval signal
    await handle.signal("admin_approval", True)

    return user_id, bucket_name

# Reject bucket creation request
async def reject_create_bucket(workflow_id: str):
    client = await create_temporal_client()

    handle = await get_workflow_handle(client, workflow_id)

    workflow_info = await handle.describe()

    user_id = workflow_info.search_attributes.get('UserId', [None])[0]
    bucket_name = workflow_info.search_attributes.get('BucketName', [None])[0]

    if workflow_info.status == 2:
        raise HTTPException(status_code=404, detail='Workflow already completed!')

    # Send approval signal
    await handle.signal("admin_approval", False)

    return user_id, bucket_name