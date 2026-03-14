from sqlalchemy import Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrderItem(Base):
    # The physical label on the PostgreSQL filing cabinet drawer for specific receipt lines
    __tablename__ = "order_items"

    # The unique barcode for this specific line on the receipt (Primary Key)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Points up to the Main Kitchen Ticket (Order).
    # Tells the database: "This sushi roll belongs to Ticket #1042."
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    
    # Points over to the Menu Board (MenuItem).
    # Tells the kitchen exactly which meal to cook (e.g., Meal #5).
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    
    # The number of plates the chef needs to make for this specific meal.
    quantity: Mapped[int] = mapped_column(Integer)
    
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))

    # Looks back up to the main Order Ticket.
    # Type `my_receipt_line.order.status` to instantly see if the whole order is ready.
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    
    # Looks back at the original Menu Board item.
    # Can type `my_receipt_line.menu_item.ingredients` to check for allergies!
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="order_items")