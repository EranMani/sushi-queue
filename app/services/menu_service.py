from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem

async def get_all_menu_items(db: AsyncSession):
    """
    The Manager walks to the PostgreSQL cabinet and asks:
    Find every MenuItem file where the 'is_available' checkbox is ticked.
    Use result.scalars().all() to grab ALL matching files and hand them back as a Python list.
    """
    result = await db.execute(select(MenuItem).where(MenuItem.is_available == True))
    return result.scalars().all()
