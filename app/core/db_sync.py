from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.database import Base
from app.models import User, MenuItem, Order, OrderItem, OrderStatus

"""
THE KITCHEN'S PRIVATE DOOR (Synchronous Database Connection)
----------------------------------------------------------------
- FastAPI waiters use 'Async' (multitasking) to handle thousands of customers at the front door.
- Celery chefs work 'Synchronously' (step-by-step).

This file builds a dedicated, standard-speed pathway for the background 
workers to access the PostgreSQL Filing Cabinet without getting confused 
by the Waiters' fast-paced async tools.
"""

# Strip the asyncpg from the database url so the Chef uses the standard Postgres connection string.
_sync_url = settings.database_url.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")


# BUILDING THE PRIVATE DOOR
# engine: The physical synchronous wire (landline) to the database. We cannot use the 
#         existing async engine from database.py because the Chefs only know how to use sync tools!
engine = create_engine(_sync_url, pool_pre_ping=True)

# SessionLocal: The Blank Clipboard Factory. We need a factory to stamp out a brand new, 
#               blank workspace for every single task so Chefs don't overwrite each other's math.
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)

# HANDING THE CHEF THE KEYS
# Give a Chef a database session when they start a task, and safely closes the drawer when they are done.
# NOTE: This is NOT used with FastAPI Depends() because the Kitchen operates outside of HTTP routes. 
# Chefs will manually grab a clipboard inside their tasks using: db = next(get_sync_db())
def get_sync_db():
    with SessionLocal() as session:
        yield session
