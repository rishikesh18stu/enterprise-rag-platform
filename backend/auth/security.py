from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
# bcrypt is the industry-standard hashing algorithm for passwords --
# deliberately slow (computationally expensive) by design, which makes
# brute-force attacks on stolen hashes impractical.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In production, this MUST come from an environment variable / secrets manager,
# never hardcoded or committed to git. Placeholder for now -- we'll fix this
# properly with .env files when we containerize in Phase 15.
SECRET_KEY = "CHANGE_ME_dev_only_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    """One-way hash -- cannot be reversed back into the original password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Re-hashes the submitted password and compares against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Creates a signed JWT containing the given claims plus an expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Verifies the JWT's signature and expiry, returning its claims if valid."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency: extracts and verifies the JWT from the
    Authorization header, returning its claims. Any protected endpoint
    just adds `user: dict = Depends(get_current_user)` to its signature.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return payload