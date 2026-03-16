import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.menu import MenuItemPublic
from app.services.menu_service import get_all_menu_items

"""
NOTE: Redis does not understand Python objects or Pydantic models; it primarily stores raw text.
postgresql -> pydantic model -> python dictionary(json) -> json.dumps (raw text) -> redis
PostgreSQL (SQLAlchemy Object)
       │
       ▼  1. MenuItemPublic.model_validate(item) 
             # Checks the ID and converts the heavy DB object into a clean Pydantic schema.
       │
The Door Guard (Pydantic Schema)
       │
       ▼  2. .model_dump(mode="json") 
             # Flattens the schema into a simple Python dictionary (making dates/IDs JSON-ready).
       │
The Clipboard (Python Dictionary)
       │
       ▼  3. json.dumps(data) 
             # Translates the Python dictionary into a pure text string.
       │
Redis Whiteboard (JSON String)

--------------------------------

NOTE: Convert redis redis note raw text -> python dictionary json (json.loads) -> secure pydantic model (MenuItemPublic.model_validate)
Redis Whiteboard (JSON String)
       │
       ▼  1. json.loads(cached) 
             # Reads the text string and translates it back into a Python dictionary.
       │
The Clipboard (Python Dictionary)
       │
       ▼  2. MenuItemPublic.model_validate(x) 
             # Validates the dictionary to ensure no data is missing, returning a safe schema.
       │
The Door Guard (Pydantic Schema)

"""

# THE MENU BOARD (Router)
router = APIRouter(prefix="/menu", tags=["menu"])

# THE WHITEBOARD SETTINGS
# Name the sticky note "menu:all" and tell it to self-destruct after 60 seconds (Time To Live).
CACHE_KEY = "menu:all"
CACHE_TTL = 60

@router.get("", response_model=list[MenuItemPublic])
async def get_menu(db: AsyncSession = Depends(get_db)):
    """
    response_model=list[MenuItemPublic]: The Exit Guard ensures we hand back a LIST of safe menu items.
    CACHE_KEY = "menu:all": The Waiter names the sticky note "menu:all".
    CACHE_TTL = 60: The Waiter tells the sticky note to self-destruct after 60 seconds (Time To Live).
    """
    # The Waiter walks over to the lightning-fast Redis Whiteboard.
    redis = await get_redis()
    cached = await redis.get(CACHE_KEY)
    
    # Is the menu already written on the whiteboard?
    if cached:
        # Parse the JSON string back into a Python list and give it to the customer instantly.
        return [MenuItemPublic.model_validate(x) for x in json.loads(cached)]

    # When the whiteboard is empty, the Waiter asks the Manager to dig through the PostgreSQL filing cabinet.
    items = await get_all_menu_items(db)
    
    # Convert the heavy database items into clean JSON text
    data = [MenuItemPublic.model_validate(i).model_dump(mode="json") for i in items]
    
    # Pin the database items to the Redis whiteboard so the NEXT customer gets it instantly!
    await redis.set(name=CACHE_KEY, ex=CACHE_TTL, value=json.dumps(data, default=str))
    
    # Hand the freshly pulled menu to the current customer.
    return [MenuItemPublic.model_validate(i) for i in items]
