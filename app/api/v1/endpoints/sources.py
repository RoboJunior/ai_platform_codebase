from fastapi import APIRouter, Depends, HTTPException
from app.casbin.enforcer import check_permission
from app.api.v1.dependencies import get_database_session
from sqlalchemy.orm import Session
from app.services.auth_service import get_current_user
from app.api.v1.schemas.source import (
    AddMinioCredentials, DeleteMinioCredentials, UpdateMinioCredentials)
from app.services.vault_service import create_secret, delete_secret, update_secret
from app.services.role_service import get_user_role

# Minio router if any new source will be added that router will be added aswell
minio_router = APIRouter()

# Add new minio client credentials
@minio_router.post('/add_minio_client_credentials')
def add_minio_client_credentials_to_vault(minio_credentials: AddMinioCredentials, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Get the team name and user role 
    user_role, team_name = get_user_role(current_user.id, minio_credentials.team_id, db)

    # Check the permission of the user
    if not check_permission(user_role, "vault", "write"):
        raise HTTPException(status_code=403, detail="User doesnt have permission to add new source")
    
    # Create the secrets in key vault
    minio_credentials_dict = {"path": f"{team_name}/minio_credentials", 
                            "minio_access_key": minio_credentials.minio_access_key, 
                            "minio_secret_key": minio_credentials.minio_secret_key,
                            "minio_server": minio_credentials.minio_server}
    
    # Add the secrets to key vault
    response = create_secret(minio_credentials_dict)
    return response

@minio_router.delete('/delete_minio_client_credentials')
def delete_minio_client_credentials(delete_credentials: DeleteMinioCredentials, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Get the team name and user role 
    user_role, team_name = get_user_role(current_user.id, delete_credentials.team_id, db)

    # Check the permission of the user
    if not check_permission(user_role, "vault", "delete"):
        raise HTTPException(status_code=403, detail="User doesnt have permission to add new source")
    
    # Delete secret from vault
    delete_secret(f"{team_name}/minio_credentials")
    return {"message": "secrets deleted successfully"}

@minio_router.put('/update_minio_client_credentials')
def update_minio_client_credentials(update_credentials: UpdateMinioCredentials, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Get the team name and user role 
    user_role, team_name = get_user_role(current_user.id, update_credentials.team_id, db)

    # Check the permission of the user
    if not check_permission(user_role, "vault", "delete"):
        raise HTTPException(status_code=403, detail="User doesnt have permission to add new source")
    
     # Create the secrets in key vault
    minio_credentials_dict = {"path": f"{team_name}/minio_credentials", 
                            "minio_access_key": update_credentials.minio_access_key, 
                            "minio_secret_key": update_credentials.minio_secret_key,
                            "minio_server": update_credentials.minio_server}

    # Update secret from vault
    response = update_secret(minio_credentials_dict)
    return response
