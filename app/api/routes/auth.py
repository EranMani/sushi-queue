from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import UserCreate, UserPublic, Token
from app.services.user_service import create_user, get_user_by_email, authenticate_user

"""
THE FRONT DESK (Router)
Group all authentication-related waiters here.
prefix="/auth" -> Every route below automatically starts with /auth (e.g., /auth/register)
tags=["auth"] -> Groups these routes together cleanly in the auto-generated API documentation (Swagger UI).
"""
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic)
async def register(
    body: UserCreate, # The Entry Guard: Requires the customer to send a valid email and password
    db: AsyncSession = Depends(get_db) # The Temporary Database Connection
):
    """
    response_model=UserPublic: The Exit Guard. Validates against the UserPublic schema. 
    Ensures we never accidentally leak the database ID or hashed password back to the customer.
    """
    # Check if the Rolodex already has this email
    if await get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Hand the valid data to the Manager to hash the password and save the file
    user = await create_user(db, body.email, body.password)
    
    # Return the full database user. FastAPI will automatically filter it through UserPublic!
    return user



@router.post("/token", response_model=Token)
async def login(
    body: UserCreate, 
    db: AsyncSession = Depends(get_db) # The Temporary Database Connection
):
    """
    The Host Stand
    response_model=Token: The Exit Guard ensures we only hand back the access_token string.
    """
    # Ask the Manager to verify the password against the database
    user = await authenticate_user(db, body.email, body.password)
    
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    # Mint a new 60-minute VIP Wristband using their database ID
    token = create_access_token(data={"sub": str(user.id)})
    
    # Hand the wristband back to the customer
    return Token(access_token=token)