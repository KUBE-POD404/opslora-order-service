from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OrderCreate, OrderResponse, OrderUpdate

from app.services.order_service import (
    create_order,
    confirm_order,
    get_order,
    cancel_order,
    list_orders,
    update_order,
)

from app.dependencies.permissions import require_permission

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/create-order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@router.post("/create-order/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order_api(
    data: OrderCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[object, Depends(require_permission("order.create"))],
):
    auth_header = request.headers.get("Authorization")

    return create_order(
        db=db,
        customer_id=data.customer_id,
        items=[item.model_dump() for item in data.items],
        organization_id=current_user.org_id,
        created_by_user_id=current_user.user_id,
        auth_header=auth_header
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_api(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[object, Depends(require_permission("order.read"))],
):
    return get_order(db, order_id, current_user.org_id)


@router.get("/", response_model=list[OrderResponse])
def list_orders_api(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[object, Depends(require_permission("order.read"))],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 15,
    status: str | None = None,
    customer_id: int | None = None
):
    offset = (page - 1) * limit

    return list_orders(
        db,
        organization_id=current_user.org_id,
        offset=offset,
        limit=limit,
        status=status,
        customer_id=customer_id
    )


@router.put("/{order_id}", response_model=OrderResponse)
def update_order_api(
    order_id: int,
    data: OrderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[object, Depends(require_permission("order.update"))],
):
    return update_order(
        db,
        order_id,
        current_user.org_id,
        [item.model_dump() for item in data.items]
    )


@router.post("/{order_id}/confirm", response_model=OrderResponse)
def confirm_order_api(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[object, Depends(require_permission("order.confirm"))],
):
    return confirm_order(db, order_id, current_user.org_id)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order_api(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[object, Depends(require_permission("order.cancel"))],
):
    return cancel_order(db, order_id, current_user.org_id)