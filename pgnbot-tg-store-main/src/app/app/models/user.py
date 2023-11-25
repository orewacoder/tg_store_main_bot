from datetime import datetime
from typing import Optional
from aiogram.types import User as AiogramUser
from pydantic import Field
from app.models.base import DBModel


class User(DBModel):
    id: int
    name: str
    total_orders: int = 0
    total_orders_amount: int = 0
    tg_data: AiogramUser = None
    joined_at: datetime = Field(default_factory=datetime.now)
    is_banned: bool = False
    is_admin: bool = False
    address: Optional[str] = None
    phone: Optional[str] = None

    _collection = "users"
