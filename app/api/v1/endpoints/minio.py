from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.api.v1.dependencies import get_database_session
from sqlalchemy.orm import Session
from app.api.v1.schemas.source import CreateMinioBucket, DeleteMinioBucket
from app.services.minio_service import (create_minio_bucket, 
        check_bucket_exist, delete_bucket, 
        list_all_buckets, create_bucket_request_temporilio,
        list_all_buckets_request_team, list_all_buckets_request_user,
        approve_create_bucket, reject_create_bucket)
from app.casbin.enforcer import check_permission
from app.services.auth_service import get_current_user
from app.services.role_service import get_user_role
from app.services.vault_service import get_secret
import json
from app.services.notification_service import start_app_notifications_workflow

minio_router = APIRouter()

# Create a bucket in minio
@minio_router.post('/create_bucket')
def create_bucket_minio(new_source: CreateMinioBucket, background_task: BackgroundTasks, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    bucket_name = new_source.bucket_name.lower().replace(' ', '')

   # Get the team name and user role 
    user_role, team_name = get_user_role(current_user.id, new_source.team_id, db)

    # Check the permission of the user
    if not check_permission(user_role, "vault", "read"):
        raise HTTPException(status_code=403, detail="User doesnt have access to get secrets from vault")

    # If the user doesnt have permission raise a http exception
    if not check_permission(user_role, 'source_minio', 'write'):
        raise HTTPException(status_code=403, detail="User doesnt have permission to create new source")
    
    # Get the secret credentials from the vault
    credentails = get_secret(f"{team_name}/minio_credentials")
    
    # If the bucket exist raise a http exception
    if check_bucket_exist(bucket_name, json.loads(credentails)):
        raise HTTPException(status_code=403, detail="Bucket already exits!")
    
    background_task.add_task(create_minio_bucket, new_source.team_id, bucket_name, json.loads(credentails), db)
    return {"message": f"new bucket created with name {bucket_name}"}

@minio_router.delete('/delete_bucket')
def delete_bucket_minio(new_source: DeleteMinioBucket, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    bucket_name = new_source.bucket_name.lower().replace(' ', '')

   # Get the team name and user role 
    user_role, team_name = get_user_role(current_user.id, new_source.team_id, db)

    # Check the permission of the user
    if not check_permission(user_role, "vault", "read"):
        raise HTTPException(status_code=403, detail="User doesnt have access to get secrets from vault")

    # If the user doesnt have permission raise a http exception
    if not check_permission(user_role, 'source_minio', 'delete'):
        raise HTTPException(status_code=403, detail="User doesnt have permission to delete a resource")
    
    # Get the secret credentials from the vault
    credentails = get_secret(f"{team_name}/minio_credentials")
    
    # If the bucket exist raise a http exception
    if not check_bucket_exist(bucket_name, json.loads(credentails)):
        raise HTTPException(status_code=403, detail="Bucket doesnt exit!")

    # create a new bucket 
    delete_bucket(bucket_name, json.loads(credentails))
    return {"message": f"bucket deleted with the name : {bucket_name}"}

@minio_router.get("/list_buckets")
def list_buckets_minio(team_id: int, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
   # Get the team name and user role 
    user_role, team_name = get_user_role(current_user.id, team_id, db)

    # Check the permission of the user
    if not check_permission(user_role, "vault", "read"):
        raise HTTPException(status_code=403, detail="User doesnt have access to get secrets from vault")

    # If the user doesnt have permission raise a http exception
    if not check_permission(user_role, 'source_minio', 'read'):
        raise HTTPException(status_code=403, detail="User doesnt have permission to get resources")
    
    # Get the secret credentials from the vault
    credentails = get_secret(f"{team_name}/minio_credentials")

    # Get all the buckets from minio
    buckets = list_all_buckets(json.loads(credentails))

    return buckets
    
@minio_router.post('/request/create_bucket')
async def create_new_bucket_request(new_source: CreateMinioBucket, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    bucket_name = new_source.bucket_name.lower().replace(' ', '')

   # Get the team name and user role 
    user_role, team_name = get_user_role(current_user.id, new_source.team_id, db)

    # Check the permission of the user
    if not check_permission(user_role, "vault", "read"):
        raise HTTPException(status_code=403, detail="User doesnt have access to get secrets from vault")

    # If the user doesnt have permission raise a http exception
    if not check_permission(user_role, 'source_minio', 'request'):
        raise HTTPException(status_code=403, detail="User doesnt have permission to create new source")

    # Create a request for bucket creation in temporilio
    workflow_id = await create_bucket_request_temporilio(current_user.id, new_source.team_id, bucket_name, team_name)
    return workflow_id

@minio_router.get("/request/create_bucket/pending_requests")
async def list_pending_buckets(team_id: int, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Get the team name and user role 
    user_role, _ = get_user_role(current_user.id, team_id, db)

    # If the user is admin return all the bucket requests
    if check_permission(user_role, "source_minio", "list_all_requests"):
        all_buckets_requests = await list_all_buckets_request_team(team_id)
        return all_buckets_requests

    # If the user is not a editor/admin he is not allowed to fetch requests.
    if not check_permission(user_role, "source_minio", "list_user_requests"):
        raise HTTPException(status_code=403, detail="User not allowed to fetch requests!")
    
    # If the user is editor return all the request they made
    user_bucket_requests = await list_all_buckets_request_user(current_user.id, team_id)

    return user_bucket_requests

@minio_router.post("/request/create_bucket/pending_requests/approve_bucket_creation")
async def approve_bucket_creation(workflow_id: str, team_id: int, background_task: BackgroundTasks, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Get the team name and user role 
    user_role, _ = get_user_role(current_user.id, team_id, db)

    # Check the user is admin of the team or not
    if not check_permission(user_role, "source_minio", "approve_request"):
        raise HTTPException(status_code=403, detail="User does not have permission to approve a request")
    
    user_id, bucket_name = await approve_create_bucket(workflow_id)

    background_task.add_task(start_app_notifications_workflow, [{"user_id": user_id}], f"Your request for bucket creation for bucket name : {bucket_name} has approved!", db)

    return {"message": "Bucket creation request approved!"}

@minio_router.post("/request/create_bucket/pending_requests/reject_bucket_creation")
async def reject_bucket_creation(workflow_id: str, team_id: int, background_task: BackgroundTasks, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Get the team name and user role 
    user_role, _ = get_user_role(current_user.id, team_id, db)

    # Check the user is admin of the team or not
    if not check_permission(user_role, "source_minio", "reject_request"):
        raise HTTPException(status_code=403, detail="User does not have permission to reject a request")
    
    # Approve bucket creation request if the user is admin
    user_id, bucket_name = await reject_create_bucket(workflow_id)

    # Send notification to the user 
    background_task.add_task(start_app_notifications_workflow, [{"user_id": user_id}], f"Your request for bucket creation for bucket name : {bucket_name} has rejected!", db)

    return {"message": "Bucket creation request rejected!"}
