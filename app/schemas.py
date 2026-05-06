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
    customer_display_name: str | None = None
    customer_phone: str | None = None
    customer_type: str | None = None
    customer_tax_id: str | None = None
    customer_gstin: str | None = None
    customer_tax_registration_type: str | None = None
    customer_place_of_supply: str | None = None
    billing_address_line1: str | None = None
    billing_address_line2: str | None = None
    billing_city: str | None = None
    billing_state: str | None = None
    billing_postal_code: str | None = None
    billing_country: str | None = None
    shipping_same_as_billing: bool | None = None
    shipping_address_line1: str | None = None
    shipping_address_line2: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_postal_code: str | None = None
    shipping_country: str | None = None
    payment_terms_days: int | None = None
    status: str
    created_at: datetime
    total: float
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)
