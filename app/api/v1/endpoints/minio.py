from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.dependencies import get_database_session
from sqlalchemy.orm import Session
from app.api.v1.schemas.source import CreateMinioBucket, DeleteMinioBucket
from app.services.minio_service import create_bucket, check_bucket_exist, delete_bucket, list_all_buckets
from app.casbin.enforcer import check_permission
from app.services.auth_service import get_current_user
from app.services.role_service import get_user_role
from app.services.vault_service import get_secret
import json

minio_router = APIRouter()

# Create a bucket in minio
@minio_router.post('/create_bucket')
def create_bucket_minio(new_source: CreateMinioBucket, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
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

    # create a new bucket 
    create_bucket(bucket_name, json.loads(credentails))
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
        raise HTTPException(status_code=403, detail="User doesnt have permission to create new source")
    
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
    
    
