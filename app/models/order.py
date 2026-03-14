import enum
from datetime import datetime
from sqlalchemy import Numeric, DateTime, func, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Use an Enum so the database strict-enforces these exact 5 words. 
class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Order(Base):
    # The physical label on the PostgreSQL filing cabinet drawer for all restaurant tickets
    __tablename__ = "orders"

    # The permanent, unique Ticket Number for this entire order (Primary Key)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # he Physical Pipe (Foreign Key) to the Customer. 
    # nullable=True means "Guest Checkouts are perfectly welcome here!"
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # The Current Status. index=True creates a Rolodex so the database 
    # can instantly find all "PREPARING" orders without checking every single ticket.
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    
    # The Final Bill: Max 10 digits total, exactly 2 digits for the cents.
    total_price: Mapped[float] = mapped_column(Numeric(10, 2))
    
    # The Manager's Auto-Stamper: The exact second the ticket was printed.
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # The Update Stamper: Starts with the creation time, but `onupdate` tells Python 
    # to stamp the current time again anytime a chef changes the status or price!
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Points back to the Customer who placed the order.
    # The `| None` matches the nullable physical pipe, warning Python it might be a guest.
    user: Mapped["User | None"] = relationship("User", back_populates="orders")
    
    # Points down to the physical food items (OrderItems) on the receipt.
    # Python hands a list[] of all the sushi rolls tied to this main ticket.
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order")