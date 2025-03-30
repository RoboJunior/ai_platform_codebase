# activity.py
from temporalio import activity
import json
from app.services.vault_service import get_secret
from sqlalchemy.orm import Session

@activity.defn
async def create_bucket(team_name: str, bucket_name: str, team_id: int, db: Session):
    try:
        from app.services.minio_service import check_bucket_exist, create_minio_bucket
        # Get the secret credentials from the vault
        credentials = get_secret(f"{team_name}/minio_credentials")
        parsed_credentials = json.loads(credentials)
        
        # If the bucket exists, raise an exception
        if check_bucket_exist(bucket_name, parsed_credentials):
            # In activities, it's better to return errors than raise HTTP-specific exceptions
            return {"success": False, "message": "Bucket already exists!"}
        
        # Create a new bucket
        await create_minio_bucket(team_id, bucket_name, parsed_credentials, db)  # Use differently named function
        return {"success": True, "message": f"Bucket {bucket_name} created successfully!"}
    except Exception as e:
        # Handle errors and return a structured response
        return {"success": False, "message": f"Error creating bucket: {str(e)}"}