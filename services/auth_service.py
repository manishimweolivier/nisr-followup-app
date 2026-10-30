"""
Authentication and Role-Based Access Control Service for FollowUp
Manages local credentials verification, user sessions, and authorization checks.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import config
from database.connection import execute_query, execute_single, execute_statement
from utils.security import verify_password, hash_password

def authenticate_user(username: str, plain_password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user against local SQLite records.
    Returns user dict on success, None on invalid credentials.
    """
    if not username or not plain_password:
        return None
        
    row = execute_single(
        """
        SELECT id, username, full_name, email, password_hash, role, facility, is_active
        FROM users
        WHERE LOWER(username) = LOWER(?) AND is_active = 1
        """,
        (username.strip(),)
    )
    
    if not row:
        return None
        
    stored_hash = row["password_hash"]
    if verify_password(plain_password, stored_hash):
        # Update last_login
        now_str = datetime.now().isoformat()
        execute_statement(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (now_str, row["id"])
        )
        
        # Log authentication action
        log_audit_action(
            username=row["username"],
            role=row["role"],
            action="USER_LOGIN",
            target_type="User",
            target_ref=row["username"],
            details="User successfully authenticated to local application session."
        )
        
        return {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
            "facility": row["facility"]
        }
        
    return None

def create_user(username: str, full_name: str, email: str, plain_password: str,
                role: str, facility: str, actor_username: str) -> Tuple[bool, str]:
    """Create a new user account (Administrator only)."""
    if not username or len(username.strip()) < 3:
        return False, "Username must be at least 3 alphanumeric characters."
    if not plain_password or len(plain_password) < 6:
        return False, "Password must be at least 6 characters."
    if role not in config.ALL_ROLES:
        return False, f"Role must be one of: {', '.join(config.ALL_ROLES)}"
        
    # Check duplicate
    existing = execute_single("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    if existing:
        return False, f"Username '{username}' already exists."
        
    now_str = datetime.now().isoformat()
    phash = hash_password(plain_password)
    
    try:
        execute_statement(
            """
            INSERT INTO users (username, full_name, email, password_hash, role, facility, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (username.strip(), full_name.strip(), email.strip(), phash, role, facility.strip(), now_str)
        )
        log_audit_action(
            username=actor_username,
            role=config.ROLE_ADMIN,
            action="CREATE_USER",
            target_type="User",
            target_ref=username,
            details=f"Created user account with role {role} for facility {facility}."
        )
        return True, "User account successfully created."
    except Exception as e:
        return False, f"Database error creating user: {str(e)}"

def update_user_status(user_id: int, is_active: int, actor_username: str) -> bool:
    """Activate or deactivate a user account."""
    execute_statement("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
    log_audit_action(
        username=actor_username,
        role=config.ROLE_ADMIN,
        action="UPDATE_USER_STATUS",
        target_type="User",
        target_ref=str(user_id),
        details=f"Updated is_active status to {is_active}."
    )
    return True

def list_all_users() -> List[Dict[str, Any]]:
    """Retrieve all users for administrative review."""
    rows = execute_query(
        """
        SELECT id, username, full_name, email, role, facility, is_active, created_at, last_login
        FROM users
        ORDER BY created_at DESC
        """
    )
    return [dict(r) for r in rows]

def check_permission(user: Optional[Dict[str, Any]], allowed_roles: List[str]) -> bool:
    """Check if the current logged in user has one of the allowed roles."""
    if not user:
        return False
    return user.get("role") in allowed_roles

def log_audit_action(username: str, role: str, action: str,
                     target_type: Optional[str] = None,
                     target_ref: Optional[str] = None,
                     details: Optional[str] = None):
    """Record an immutable audit log entry."""
    now_str = datetime.now().isoformat()
    try:
        execute_statement(
            """
            INSERT INTO audit_logs (timestamp, username, role, action, target_type, target_ref, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (now_str, username, role, action, target_type, target_ref, details)
        )
    except Exception:
        pass  # Audit logging should never break main flow
