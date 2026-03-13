"""
This file sets up the database connection and session management for FastAPI.

VISUAL FLOW (The Restaurant Analogy)
---------------------------------------
User Request arrives (Customer walks in)
    ↓
get_db() called (Host greets customer)
    ↓
AsyncSessionLocal() (Waiter grabs a blank notepad)
    ↓
yield session (Waiter goes to the customer's table and PAUSES to take their order)
    ↓
route handler uses session (Customer orders, e.g. db.execute(...))
    ↓
route handler returns (Order is complete)
    ↓
commit() or rollback() (Send order to kitchen OR cancel if customer leaves)
    ↓
session.close() (Waiter throws away the used notepad page, goes back to standby)
    ↓
Response sent (Food delivered!)
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# ---------------------------------------------------------------------------
# 1. THE ENGINE (The Restaurant Manager & Waiter Pool)
# ---------------------------------------------------------------------------
"""
Establishing a brand new connection to PostgreSQL takes time and computer power.
It's like hiring and training a new waiter for every single customer, only to fire 
them right after. To fix this, we build a Connection Pool. 
"""
# The engine acts like a smart restaurant manager:
engine = create_async_engine(
    settings.database_url,
    pool_size=10, # The manager keeps a permanent staff of 10 waiters (connections) open and ready
    max_overflow=20, # The manager brings in extra 20 waiters as backup when 10 primary waiters are busy. 
    # These extra connections are closed when the rush is over, to save server memory
)


# ---------------------------------------------------------------------------
# 2. THE SESSION FACTORY (The Waiter's Notepad)
# ---------------------------------------------------------------------------
"""
If the engine provides the waiter (the connection), the session is the notepad. 
It gives each request a temporary, isolated workspace so User A's data doesn't 
mix up with User B's data before being permanently saved (committed).
"""
# NOTE: A commit() saves the data permanently to the kitchen (DB)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession, 
    expire_on_commit=False, # The notepad is not erased immediately after saving, keeping the data available so fastapi 
    # can return the saved user data to frontend without making an expensive second trip to the database.
    autocommit=False, 
    autoflush=False, 
)

# ---------------------------------------------------------------------------
# 3. THE BASE CLASS 
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base for sqlalchemy models. All models inherit from this."""
    pass


# ---------------------------------------------------------------------------
# 4. DEPENDENCY INJECTION (The Order Process)
# ---------------------------------------------------------------------------
async def get_db():
    """
    FastAPI dependency that yields a db session per request.
    
    Why 'yield'? 
    Instead of returning a session and immediately shutting down, 'yield' acts 
    like a pause button. It hands the notepad to the FastAPI route and waits 
    patiently in the background. Once the route is done, it unpauses to clean up!
    """
    async with AsyncSessionLocal() as session:
        try:
            # 1. Hand the notepad to the route handler and PAUSE.
            yield session
            
            # 2. If the route finishes with no errors, save work permanently.
            await session.commit()
            
        except Exception:
            # 3. If the route crashes (e.g. bad data), cancel everything 
            # so the database doesn't get corrupted.
            await session.rollback()
            raise
            
        finally:
            # 4. No matter what happens, tear off the notepad sheet and 
            # send the waiter back to the manager's pool for the next person.
            await session.close()

"""
-------------------------
Usage example:
-------------------------
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
"""