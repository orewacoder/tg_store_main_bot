from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.utils.generators import generate_id


class Inventory(BaseModel):
    id: str = Field(default_factory=generate_id)
    product_id: str
    value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sold_at: Optional[datetime] = None
    buyer: Optional[str] = None
