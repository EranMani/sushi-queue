"""
User Lifecycle & Security Flows:

1. NEW USER REGISTRATION (The Registration Desk)
   Client -> POST /users (Sends: Email + Password)
       |
       |-> hash_password() 
       |-> Save new profile to Database 
       '-> Return Success (Wait for user to log in)

2. EXISTING USER LOGIN (The Host Stand)
   Client -> POST /api/auth/token (Sends: Email + Password)
       |
       |-> Search DB by Email (Rolodex) 
       |-> verify_password(plain, hashed) 
       |-> create_access_token(sub=user_id) 
       '-> Return JWT (Valid for 60 mins)

3. PROTECTED REQUEST (The Bouncer)
   Client -> GET /orders (Sends: Authorization: Bearer <token>)
       |
       |-> decode_access_token() (Fails if expired > 60 mins)
       |-> Extract "sub" (User ID)
       |-> Check DB: Does this User ID still exist?
       |      ├── YES -> Let them in! 
       |      └── NO  -> 401 Unauthorized (User deleted account) 
       '-> Execute Route
"""

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Annotated

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

# THE BOUNCER: OAuth2PasswordBearer
# Instructs FastAPI to intercept protected requests and look for the 'Authorization: Bearer <token>' header.
# If missing, it automatically rejects the request and points the client to the login URL (/api/auth/token).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# --- 1. PASSWORD MANAGEMENT ---
def hash_password(plain: str) -> str:
    """
    HASHING: Converts a plaintext password into an irreversible hash.
    - bcrypt strictly requires raw bytes (utf-8 encoding), not strings.
    - gensalt() adds random data before hashing, ensuring identical passwords yield unique hashes (defeats rainbow tables).
    """
    pwd_bytes = plain.encode('utf-8')
    hashed_bytes = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """
    VERIFICATION: Validates a login attempt.
    We NEVER decrypt the stored hash. Instead, bcrypt runs the same algorithm on the plaintext guess 
    and checks if the resulting bytes perfectly match the stored bytes in the database.
    """
    pwd_bytes = plain.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


# --- 2. WRISTBAND (TOKEN) MANAGEMENT ---
def create_access_token(data: dict) -> str:
    """
    JWT (Json Web Token) MINTING: Creates a state-less authentication token.
    - Embeds the 'sub' (subject/user ID) and an 'exp' (expiration timestamp in UTC).
    - Cryptographically signs the token using the server's secret_key (our unforgeable wax seal).
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

def decode_access_token(token: str) -> dict | None:
    """
    JWT VALIDATION: Recomputes the signature using our secret_key. 
    Returns None if the token was tampered with, forged, or if the 'exp' time has passed.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        return None

# --- 3. THE MASTER GATE (DEPENDENCY) ---
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    db: AsyncSession = Depends(get_db)
) -> "User":
    """
    THE GATEWAY: A FastAPI Dependency injected before any protected route.
    It chains together token validation, subject extraction, and a database fallback check.
    """
    from app.models.user import User

    # Cryptographically validate the token and check expiration.
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
        
    # Extract the subject (the string representation of the User ID).
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    # Database Fallback: Ensure the user still exists in the system.
    # This prevents deleted or banned users from exploiting previously issued, unexpired tokens.
    result = await db.execute(select(User).where(User.id == int(sub)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or inactive")
        
    # Inject the fully verified SQLAlchemy User object into the route.
    return user


# --- TESTING AREA ---
if __name__ == "__main__":
    print("\n--- 🌪️ TESTING PASSWORD BLENDER ---")
    my_password = "ilovesushi"
    print(f"1. Original: {my_password}")
    scrambled = hash_password(my_password)
    print(f"2. Scrambled (bcrypt): {scrambled}")
    print(f"3. Login match: {verify_password('ilovesushi', scrambled)} ✅")
    print(f"4. Login fail: {verify_password('wrong', scrambled)} ❌\n")

    print("--- 🎟️ TESTING JWT WRISTBAND ---")
    user_data = {"sub": "1"}
    print(f"1. Payload: {user_data}")
    token = create_access_token(user_data)
    print(f"2. JWT:\n   {token}\n")
    print(f"3. Decoded: {decode_access_token(token)} 🔍\n")