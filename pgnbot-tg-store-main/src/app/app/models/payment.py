from datetime import datetime
from pydantic import BaseModel, Field

from app.models.base import DBModel
from app.utils.generators import generate_id


class Payment(DBModel):
    id: str = Field(default_factory=generate_id)
    date: datetime = Field(default_factory=datetime.now)
    user_id: int
    order_id: int
    amount: float
    coin_amount: float = 0.0
    status: str = "pending"
    data: dict = None

    _collection = "payments"
