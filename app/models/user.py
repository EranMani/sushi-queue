from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

"""
VISUAL EXPLANATION: The Official Customer Profile Template
-----------------------------------------------------------
If PostgreSQL is the giant metal filing cabinet in the back office, this file 
is the exact form waiters MUST use when a new customer registers. 

The "Two Bosses" Rule:
Every line has two parts because we are talking to two different systems:
1. Mapped[type]: Tells Python/VS Code what the data is (for auto-complete).
2. mapped_column(): Tells the PostgreSQL database exactly how to store it on the hard drive.
"""

class User(Base):
    # THE FILING CABINET DRAWER
    # The label on the specific drawer. All filled-out forms go into the "users" drawer.
    __tablename__ = "users"

    # THE VIP TICKET NUMBER
    # primary_key=True means no two people share an ID. 
    # autoincrement=True acts like a deli-counter ticket dispenser, automatically handing out #1, #2, #3...
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # THE ROLODEX
    # String(255) limits the length. unique=True prevents duplicate registrations.
    # index=True creates a fast-lookup "Rolodex" so finding the user during login is blazing fast!
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    # Passwords are mathematically scrambled (hashed) before being saved here.
    hashed_password: Mapped[str] = mapped_column(String(255))
    
    # A simple checkbox on the form (True/False). Defaults to False (meaning they are human).
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # THE SELF-INKING TIMESTAMP
    # server_default=func.now() automatically stamps the exact time the form goes into the cabinet.
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # THE MAGIC THREAD (ORM Relationship)
    # PostgreSQL keeps order receipts in a totally separate drawer. 
    # This relationship creates a virtual thread connecting this Customer Profile 
    # directly to all their order receipts, making it easy to type `user.orders` in Python.
    # back_populates="user" means the Order receipt also has a thread pointing back here.
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")