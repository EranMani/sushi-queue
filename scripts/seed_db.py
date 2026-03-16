import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import User, MenuItem
from app.core.security import hash_password

MENU_ITEMS = [
    {"name": "Salmon Nigiri", "category": "Nigiri", "price": 6.50, "prep_time_seconds": 90, "ingredients": {"salmon": 1, "rice": 1}},
    {"name": "Tuna Nigiri", "category": "Nigiri", "price": 7.00, "prep_time_seconds": 90, "ingredients": {"tuna": 1, "rice": 1}},
    {"name": "Dragon Roll", "category": "Roll", "price": 14.00, "prep_time_seconds": 180, "ingredients": {"eel": 1, "cucumber": 1, "avocado": 1, "rice": 2}},
    {"name": "California Roll", "category": "Roll", "price": 8.50, "prep_time_seconds": 120, "ingredients": {"crab": 1, "avocado": 1, "cucumber": 1, "rice": 1}},
    {"name": "Spicy Tuna Roll", "category": "Roll", "price": 11.00, "prep_time_seconds": 150, "ingredients": {"tuna": 1, "spicy_mayo": 1, "rice": 1}},
    {"name": "Miso Soup", "category": "Soup", "price": 3.50, "prep_time_seconds": 60, "ingredients": {"miso": 1, "tofu": 1, "seaweed": 1}},
    {"name": "Edamame", "category": "Starter", "price": 4.00, "prep_time_seconds": 45, "ingredients": {"edamame": 1}},
    {"name": "Tempura Udon", "category": "Noodle", "price": 12.00, "prep_time_seconds": 240, "ingredients": {"udon": 1, "tempura": 2, "broth": 1}},
    {"name": "Green Tea Ice Cream", "category": "Dessert", "price": 5.00, "prep_time_seconds": 30, "ingredients": {"ice_cream": 1}},
    {"name": "Unagi Don", "category": "Bowl", "price": 16.00, "prep_time_seconds": 200, "ingredients": {"eel": 1, "rice": 2, "sauce": 1}},
]

async def seed():
    async with AsyncSessionLocal() as db:
        # Seed bot user
        result = await db.execute(select(User).where(User.email == "bot@sushi.local"))
        if result.scalar_one_or_none() is None:
            bot = User(
                email="bot@sushi.local",
                hashed_password=hash_password("bot-secret"),
                is_bot=True,
            )

            db.add(bot)
            await db.flush()
            print(f"Bot user created: {bot.email}")

        # seed menu items
        for item_data in MENU_ITEMS:
            result = await db.execute(select(MenuItem).where(MenuItem.name == item_data["name"]))
            if result.scalar_one_or_none() is None:
                item = MenuItem(**item_data)
                db.add(item)
                print(f"Created menu item: {item_data['name']}")

        await db.commit()
    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed())