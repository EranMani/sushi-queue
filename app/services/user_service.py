from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password, verify_password

async def create_user(db: AsyncSession, email: str, password: str, is_bot: bool = False) -> User:
    """
    Register a new customer
    Fill out the official database form (User model)
    Hash the plain password before storing it.
    """
    
    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_bot=is_bot,
    )
    
    # The manager writes the new customer's details on their temporary clipboard.
    # NOTE: PostgreSQL doesn't know about this yet! It only exists in Python memory.
    db.add(user)
    
    # The manager tells PostgreSQL to temporarily put this user in the cabinet 
    # NOTE: and generate an ID, but leaves the drawer open (doesn't permanently commit yet).
    await db.flush()

    # The manager looks at the open drawer and copies the newly generated 
    # NOTE: database ID (like id=42) back onto their clipboard and Python variable.
    await db.refresh(user)
    
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Find a customer quickly in database using their email.
    """
    # Spin the Rolodex to find the exact file matching this email.
    result = await db.execute(select(User).where(User.email == email))
    # scalar_one_or_none() means: "Give me the User profile, or None if they don't exist."
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Verify a customer at the Host Stand
    """
    # Find the user in the database using their email.
    user = await get_user_by_email(db, email)
    
    if user is None:
        return None

    # Check their password guess against the saved hash
    if not verify_password(password, user.hashed_password):
        return None

    # Return the verified profile
    return user
