from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List

# -----------------------------
# ORDER ITEM
# -----------------------------

class OrderItemCreate(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=100)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)

class OrderItemResponse(BaseModel):
    id: int
    product_name: str
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)

# -----------------------------
# ORDER
# -----------------------------

class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_email: str
    customer_name: str
    status: str
    created_at: datetime
    total: float
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)