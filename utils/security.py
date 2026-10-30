"""
Security and Cryptographic Utilities for FollowUp
Provides secure password hashing, verification, and reference code generation.
"""

import os
import hashlib
import secrets
from typing import Tuple

try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False

PBKDF2_ITERATIONS = 120000

def hash_password(password: str) -> str:
    """
    Securely hash a password using PBKDF2-HMAC-SHA256 with a unique random salt,
    or bcrypt when available. Returns a formatted string storing salt and hash.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")
    
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against the stored secure hash.
    Safe against timing attacks via hmac.compare_digest.
    """
    if not plain_password or not hashed_password:
        return False
    
    try:
        parts = hashed_password.split('$')
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            stored_hash = bytes.fromhex(parts[3])
            
            dk = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, iterations)
            return secrets.compare_digest(dk, stored_hash)
        
        # Fallback check for standard bcrypt string if generated externally
        if _HAS_BCRYPT and hashed_password.startswith(("$2b$", "$2a$")):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            
        return False
    except Exception:
        return False

def generate_reference(prefix: str, sequence_num: int, year: int = 2026) -> str:
    """Generate a clean, standardized healthcare reference ID."""
    clean_prefix = prefix.strip().upper()
    return f"{clean_prefix}-{year}-{sequence_num:04d}"
