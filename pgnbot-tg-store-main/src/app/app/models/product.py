from typing import Optional
from aiogram.types import File
from pydantic import Field
from app.models.base import DBModel
from app.utils.generators import generate_id


class Product(DBModel):
    id: str = Field(default_factory=generate_id)
    name: str
    description: str
    price: float
    photo: Optional[str] = None
    file: Optional[File] = None
    is_active: bool = True
    quantity: int = 0
    _collection = "products"
