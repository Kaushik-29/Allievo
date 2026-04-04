from datetime import datetime, timedelta
from typing import Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib
from app.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_device_id(device_id: str) -> str:
    """SHA-256 hash of Android Device ID (stored, never raw ID)."""
    return hashlib.sha256(device_id.encode()).hexdigest()


def _get_fernet_key() -> bytes:
    """Derive a valid 32-byte Fernet key from config."""
    raw = settings.FIELD_ENCRYPTION_KEY.encode()
    key = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_token(plaintext: str) -> str:
    """Encrypt OAuth tokens before storing in DB."""
    f = Fernet(_get_fernet_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt stored OAuth token."""
    f = Fernet(_get_fernet_key())
    return f.decrypt(ciphertext.encode()).decode()
