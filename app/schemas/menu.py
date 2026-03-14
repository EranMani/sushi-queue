from pydantic import BaseModel

# The Printed Menu Board (Data going OUT)
# Show this format Whenever a customer opens the app and asks, "What is on the menu?",
class MenuItemPublic(BaseModel):
    id: int
    name: str
    category: str
    price: float
    prep_time_seconds: int
    is_available: bool
    
    # Ingredients might be empty (None), so we tell Pydantic that is totally fine.
    ingredients: dict | None = None

    # The Magic Translator
    # Reads the SQLAlchemy menu item from the database and magically 
    # translates it into clean JSON for the frontend app.
    model_config = {"from_attributes": True}
