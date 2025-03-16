import hvac
from app.core.config import get_settings
import json

# Create a vault client
client = hvac.Client(url=get_settings().VAULT_SERVER)

# Create secret in vault 
def create_secret(data: dict):
    # Check if authenticated
    if not client.is_authenticated():
        raise Exception("Vault authentication failed")

    secret_data = {
        "minio_access_key": data["minio_access_key"],
        "minio_secret_key": data["minio_secret_key"],
        "minio_server": data["minio_server"]
    }
    
    create_response = client.secrets.kv.v2.create_or_update_secret(
                        mount_point="secret",
                        path=f"{data['path']}", 
                        secret=secret_data)

    return json.dumps(create_response, indent=4, sort_keys=True)

# Delete secret from vault
def delete_secret(path: str):
    # Check if authenticated
    if not client.is_authenticated():
        raise Exception("Vault authentication failed")
    
    # Permanently delete the entire secret (all versions & metadata)
    client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)

# Fetch secret from vault
def get_secret(path: str):
    # Check if authenticated
    if not client.is_authenticated():
        raise Exception("Vault authentication failed")
    
    response = client.secrets.kv.v2.read_secret_version(path=path)
    secret_data = response['data']['data']
    return json.dumps(secret_data, indent=4)

# Update secret from vault
def update_secret(data: dict):
    # Check if authenticated
    if not client.is_authenticated():
        raise Exception("Vault authentication failed")
    
    secret_data = {
        "minio_access_key": data["minio_access_key"],
        "minio_secret_key": data["minio_secret_key"],
        "minio_server": data["minio_server"]
    }
    
    # Updating secret
    update_response = client.secrets.kv.v2.create_or_update_secret(
        mount_point="secret",
        path=data['path'],
        secret=secret_data
    )
    
    return json.dumps(update_response, indent=4, sort_keys=True)

