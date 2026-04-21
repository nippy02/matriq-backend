from __future__ import annotations
from datetime import datetime, timedelta, timezone
import hashlib

import jwt
from fastapi import Depends, Header, HTTPException
from passlib.context import CryptContext

from ..config import JWT_ALGORITHM, JWT_SECRET, ROLE_ADMIN, TOKEN_EXPIRE_MINUTES
from ..database import fetchone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _password_matches(raw_password: str, stored_password_hash: str | None) -> bool:
    if not stored_password_hash:
        return False

    # legacy plain-text support
    if raw_password == stored_password_hash:
        return True

    # legacy sha256 support
    if hashlib.sha256(raw_password.encode("utf-8")).hexdigest() == stored_password_hash:
        return True

    # bcrypt / pgcrypto-compatible support
    try:
        if stored_password_hash.startswith("$2a$") or stored_password_hash.startswith("$2b$") or stored_password_hash.startswith("$2y$"):
            return pwd_context.verify(raw_password, stored_password_hash)
    except Exception:
        pass

    return False


def authenticate(login_identifier: str, password: str):
    user = fetchone(
        '''
        SELECT user_id, username, password_hash, full_name, role, branch_id, is_active
        FROM users
        WHERE lower(username) = lower(%s)
        ''',
        (login_identifier,),
    )
    if not user or not user.get('is_active'):
        return None
    if not _password_matches(password, user.get('password_hash')):
        return None
    return user


def create_token(user: dict) -> str:
    payload = {
        'sub': user['username'],
        'user_id': user['user_id'],
        'role': user['role'],
        'name': user.get('full_name') or user['username'],
        'branch_id': user.get('branch_id'),
        'exp': datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing bearer token.')
    token = authorization.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid or expired token.')
    return {
        'email': payload['sub'],
        'username': payload['sub'],
        'user_id': payload['user_id'],
        'role': payload['role'],
        'name': payload['name'],
        'branch_id': payload.get('branch_id'),
        'is_admin': payload['role'] == ROLE_ADMIN,
    }


def require_roles(*roles):
    def dep(user=Depends(current_user)):
        if roles and user['role'] not in roles:
            raise HTTPException(status_code=403, detail='User role is not allowed to access this endpoint.')
        return user

    return dep