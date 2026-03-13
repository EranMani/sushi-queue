from sqlalchemy import String, Numeric, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MenuItem(Base):
    # The physical label on the PostgreSQL filing cabinet drawer
    __tablename__ = "menu_items"

    # The permanent, unchanging VIP ticket number (Primary Key)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # index=True creates a "Rolodex" so the database can search for names instantly
    name: Mapped[str] = mapped_column(String(255), index=True)
    
    category: Mapped[str] = mapped_column(String(100))
    
    # Strict price tag rules: 10 total digits allowed, exactly 2 after the decimal (e.g., 99999999.99)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    
    prep_time_seconds: Mapped[int] = mapped_column(Integer)
    
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # JSONB acts as a flexible box to hold an entire dictionary of ingredients. 
    # nullable=True tells the database it is perfectly fine if this box is left empty.
    ingredients: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # The Magic Bridge (Python Boss)
    # Creates a virtual thread allowing Python to instantly grab all receipts (OrderItems) 
    # for this meal. 'back_populates' looks for the variable named "menu_item" on the receipt.
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="menu_item")