from pydantic import BaseModel

class AddMinioCredentials(BaseModel):
    team_id: int
    minio_access_key: str
    minio_secret_key: str
    minio_server: str

class CreateMinioBucket(BaseModel):
    team_id: int
    bucket_name: str

class DeleteMinioBucket(CreateMinioBucket):
    pass

class DeleteMinioCredentials(BaseModel):
    team_id: int

class UpdateMinioCredentials(AddMinioCredentials):
    pass