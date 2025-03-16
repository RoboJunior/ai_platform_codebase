import casbin
import casbin_sqlalchemy_adapter
from sqlalchemy import create_engine
from app.core.config import get_settings, Config

# Create the database url
DATABASE_URL = Config.DB_CONFIG.format(get_settings().DATABASE_NAME)

# Create the sqlalchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Initialize Casbin Enforcer with SQLAlchemy adapter for policy storage
adapter = casbin_sqlalchemy_adapter.Adapter(engine)
enforcer = casbin.Enforcer("app/casbin/rbac_models.conf", adapter)

# Function to reload policies from storage
def reload_policy():
    enforcer.load_policy()

# Function to check if a role has permission to perform an action on a resource
def check_permission(role: str, resource: str, action: str) -> bool:
    return enforcer.enforce(role, resource, action)

# Function to add a new policy
def add_policy(role: str, resource: str, action: str) -> bool:
    return enforcer.add_policy(role, resource, action)

# Function to remove a policy
def remove_policy(role: str, resource: str, action: str) -> bool:
    return enforcer.remove_policy(role, resource, action)

# Function to get all policies
def get_policies():
    return enforcer.get_policy()

# Function to add a group inheritance (role hierarchy)
def add_role_inheritance(role: str, inherited_role: str) -> bool:
    return enforcer.add_grouping_policy(role, inherited_role)

# Function to remove a group inheritance
def remove_role_inheritance(role: str, inherited_role: str) -> bool:
    return enforcer.remove_grouping_policy(role, inherited_role)

# Get all role inheritance relationships
def get_role_inheritance():
    return enforcer.get_grouping_policy()

# Clear all policies
def clear_policies():
    enforcer.clear_policy()
    return True

# Function to save policies to storage
def save_policies():
    return enforcer.save_policy()