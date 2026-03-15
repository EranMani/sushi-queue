from pydantic import BaseModel

from app.models.order import OrderStatus

class OrederItemCreate(BaseModel):
    menu_item_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: list[OrederItemCreate]

class OrderItemPublic(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}

class OrderPublic(BaseModel):
    id: int
    user_id: int | None
    status: OrderStatus
    total_price: float
    items: list[OrderItemPublic] = []

    model_config = {"from_attributes": True}