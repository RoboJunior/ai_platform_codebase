from typing import Dict, List, Tuple
from .enforcer import enforcer, clear_policies, save_policies, add_policy, remove_policy

# Define default policies for standard roles
DEFAULT_POLICIES: Dict[str, List[Tuple[str, str]]] = {
    "admin": [
        ("files", "read"),
        ("files", "write"),
        ("files", "update"),
        ("files", "delete"),
        ("source_minio", "read"),
        ("source_minio", "write"),
        ("source_minio", "delete"),
        ("vault", "read"),
        ("vault", "write"),
        ("vault", "update"),
        ("vault", "delete")
    ],
    "editor": [
        ("files", "read"),
        ("files", "create"),
        ("files", "update"),
        ("source_minio", "read"),
        ("vault", "read")
    ],
    "viewer": [
        ("files", "read")
    ]
}

# Role inheritance relationships
DEFAULT_ROLE_HIERARCHY = [
    ("admin", "editor"),
    ("editor", "viewer")
]

def initialize_policies():
    """
    Initialize Casbin policies based on roles in the database.
    Should be run once during app setup.
    """
    # Clear existing policies to avoid duplicates
    clear_policies()
    
    # Get all roles from your database
    roles = ['admin', 'viewer', 'editor']
    
    # Add policies for each role based on default policies
    for role in roles:
        # Add default policies if they exist for this role
        if role in DEFAULT_POLICIES:
            for resource, action in DEFAULT_POLICIES[role]:
                enforcer.add_policy(role, resource, action)
                
    # Set up role hierarchy
    for parent_role, child_role in DEFAULT_ROLE_HIERARCHY:
        enforcer.add_grouping_policy(parent_role, child_role)
                
    # Save policies to storage
    save_policies()
    
    return True

def add_custom_policy(role: str, resource: str, action: str):
    """
    Add a custom policy for a specific role, resource, and action
    """
    result = add_policy(role, resource, action)
    save_policies()
    return result

def remove_custom_policy(role: str, resource: str, action: str):
    """
    Remove a custom policy
    """
    # result = enforcer.remove_policy(role, resource, action)
    result = remove_policy(role, resource, action)
    save_policies()
    return result

def get_role_policies(role: str):
    """
    Get all policies for a specific role
    """
    # Filter policies where the role is the subject
    return enforcer.get_filtered_policy(0, role)

if __name__ == "__main__":
    initialize_policies()