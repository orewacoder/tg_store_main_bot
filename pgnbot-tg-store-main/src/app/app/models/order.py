from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from app.models.base import DBModel
from app.utils.generators import generate_id


class SelectedProducts(BaseModel):
    name: str
    product_id: str
    quantity: int
    total_price: float = 0.0


class SupportedCoin(str, Enum):
    BTC = "BTC"
    LTC = "LTC"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID_PARTIALLY = "paid_partially"
    PAID = "paid"
    CANCELED = "canceled"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class Cart(DBModel):
    id: str = Field(default_factory=generate_id)
    user_id: int
    products: list[SelectedProducts]
    total_amount: float = 0.0
    total_coin_amount: float = 0.0
    coin: SupportedCoin = SupportedCoin.BTC
    closed: bool = False

    _collection = "carts"


class Order(DBModel):
    id: str = Field(default_factory=generate_id)
    date: datetime = Field(default_factory=datetime.now)
    user_id: int
    cart_id: str
    payment_status: bool = False
    paid_amount: float = 0.0
    paid_coin_amount: float = 0.0
    user_comments: str = ""
    status: OrderStatus = OrderStatus.PENDING
    _collection = "orders"
