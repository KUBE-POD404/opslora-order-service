import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem

from app.exceptions.custom_exceptions import NotFoundException, ConflictException
from app.utils.service_client import authenticated_get

from app.core.celery_app import celery
from app.core.config import settings

logger = logging.getLogger(__name__)

CUSTOMER_SERVICE_URL = settings.customer_service_url
API_VERSION = settings.api_version


# -----------------------------
# VALIDATE + FETCH CUSTOMER
# -----------------------------
def fetch_customer(customer_id: int, auth_header: str):

    url = f"{CUSTOMER_SERVICE_URL}{API_VERSION}/customers/{customer_id}/order-snapshot"

    response = authenticated_get(url, auth_header)
    logger.info("Calling customer service", extra={"url": url})

    if response.status_code != 200:
        raise NotFoundException("Customer not found")

    data = response.json()
    customer_email = data.get("email")
    customer_name = data.get("name") or data.get("customer_name")

    if not customer_email or not customer_name:
        raise ConflictException("Invalid customer service response")

    return {
        "email": customer_email,
        "name": customer_name,
        "display_name": data.get("display_name"),
        "phone": data.get("phone"),
        "customer_type": data.get("customer_type"),
        "tax_id": data.get("tax_id"),
        "gstin": data.get("gstin"),
        "tax_registration_type": data.get("tax_registration_type"),
        "place_of_supply": data.get("place_of_supply"),
        "billing_address_line1": data.get("billing_address_line1"),
        "billing_address_line2": data.get("billing_address_line2"),
        "billing_city": data.get("billing_city"),
        "billing_state": data.get("billing_state"),
        "billing_postal_code": data.get("billing_postal_code"),
        "billing_country": data.get("billing_country"),
        "shipping_same_as_billing": data.get("shipping_same_as_billing"),
        "shipping_address_line1": data.get("shipping_address_line1"),
        "shipping_address_line2": data.get("shipping_address_line2"),
        "shipping_city": data.get("shipping_city"),
        "shipping_state": data.get("shipping_state"),
        "shipping_postal_code": data.get("shipping_postal_code"),
        "shipping_country": data.get("shipping_country"),
        "payment_terms_days": data.get("payment_terms_days"),
    }


# -----------------------------
# HELPER: BUILD PAYLOAD
# -----------------------------
def build_order_payload(order: Order, items: list):
    return {
        "order_id": order.id,
        "customer_id": order.customer_id,
        "organization_id": order.organization_id,
        "email": order.customer_email,
        "customer_name": order.customer_name,
        "customer_display_name": order.customer_display_name,
        "customer_phone": order.customer_phone,
        "customer_type": order.customer_type,
        "customer_tax_id": order.customer_tax_id,
        "customer_gstin": order.customer_gstin,
        "customer_tax_registration_type": order.customer_tax_registration_type,
        "customer_place_of_supply": order.customer_place_of_supply,
        "items": items
    }


# -----------------------------
# GET ORDER DB (CORE)
# -----------------------------
def get_order_db(
    db: Session,
    order_id: int,
    organization_id: int,
) -> Order:

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.organization_id == organization_id
        )
        .first()
    )

    if not order:
        raise NotFoundException("Order not found")

    return order


# -----------------------------
# ATTACH ITEMS + TOTAL
# -----------------------------
def attach_order_details(db: Session, order: Order):

    items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    order.items = items
    order.total = sum(item.quantity * item.unit_price for item in items)

    return order


# -----------------------------
# CREATE ORDER
# -----------------------------
def create_order(
    db: Session,
    customer_id: int,
    items: list,
    organization_id: int,
    created_by_user_id: int,
    auth_header: str
) -> Order:

    logger.info("Creating order", extra={"customer_id": customer_id})

    customer = fetch_customer(customer_id, auth_header)

    order = Order(
        organization_id=organization_id,
        customer_id=customer_id,
        customer_email=customer["email"],
        customer_name=customer["name"],
        customer_display_name=customer.get("display_name"),
        customer_phone=customer.get("phone"),
        customer_type=customer.get("customer_type"),
        customer_tax_id=customer.get("tax_id"),
        customer_gstin=customer.get("gstin"),
        customer_tax_registration_type=customer.get("tax_registration_type"),
        customer_place_of_supply=customer.get("place_of_supply"),
        billing_address_line1=customer.get("billing_address_line1"),
        billing_address_line2=customer.get("billing_address_line2"),
        billing_city=customer.get("billing_city"),
        billing_state=customer.get("billing_state"),
        billing_postal_code=customer.get("billing_postal_code"),
        billing_country=customer.get("billing_country"),
        shipping_same_as_billing=customer.get("shipping_same_as_billing"),
        shipping_address_line1=customer.get("shipping_address_line1"),
        shipping_address_line2=customer.get("shipping_address_line2"),
        shipping_city=customer.get("shipping_city"),
        shipping_state=customer.get("shipping_state"),
        shipping_postal_code=customer.get("shipping_postal_code"),
        shipping_country=customer.get("shipping_country"),
        payment_terms_days=customer.get("payment_terms_days"),
        status="CREATED",
        created_by_user_id=created_by_user_id,
        created_at=datetime.now(timezone.utc),
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    for item in items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
        )

    db.commit()

    logger.info("Order created", extra={"order_id": order.id})

    celery.send_task(
        "notification.send_order_created_email",
        args=[{
            "payload": build_order_payload(order, items)
        }],
        queue="notification_queue"
    )

    return get_order(db, order.id, organization_id)


# -----------------------------
# GET ORDER (API)
# -----------------------------
def get_order(
    db: Session,
    order_id: int,
    organization_id: int,
) -> Order:

    order = get_order_db(db, order_id, organization_id)
    return attach_order_details(db, order)


# -----------------------------
# LIST ORDERS
# -----------------------------
def list_orders(
    db: Session,
    organization_id,
    offset=0,
    limit=15,
    status=None,
    customer_id=None
):

    query = db.query(Order).filter(Order.organization_id == organization_id)

    if status:
        query = query.filter(Order.status == status)

    if customer_id:
        query = query.filter(Order.customer_id == customer_id)

    orders = (
        query.order_by(Order.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [attach_order_details(db, order) for order in orders]


# -----------------------------
# UPDATE ORDER
# -----------------------------
def update_order(db: Session, order_id: int, organization_id: int, items: list):

    order = get_order_db(db, order_id, organization_id)

    if order.status != "CREATED":
        raise ConflictException("Only CREATED orders can be updated")

    db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()

    for item in items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
        )

    db.commit()

    return get_order(db, order.id, organization_id)


# -----------------------------
# CONFIRM ORDER
# -----------------------------
def confirm_order(db: Session, order_id: int, organization_id: int):

    order = get_order_db(db, order_id, organization_id)

    if order.status != "CREATED":
        raise ConflictException("Only CREATED orders can be confirmed")

    order.status = "CONFIRMED"
    db.commit()
    db.refresh(order)

    logger.info("Order confirmed", extra={"order_id": order.id})

    items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    items_payload = [
        {
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price
        }
        for item in items
    ]

    celery.send_task(
        "notification.send_order_confirmed_email",
        args=[{
            "payload": build_order_payload(order, items_payload)
        }],
        queue="notification_queue"
    )

    return attach_order_details(db, order)


# -----------------------------
# CANCEL ORDER
# -----------------------------
def cancel_order(db: Session, order_id: int, organization_id: int):

    order = get_order_db(db, order_id, organization_id)

    if order.status == "CONFIRMED":
        raise ConflictException("Confirmed orders cannot be cancelled")

    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)

    logger.info("Order cancelled", extra={"order_id": order.id})

    items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    items_payload = [
        {
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price
        }
        for item in items
    ]

    celery.send_task(
        "notification.send_order_cancelled_email",
        args=[{
            "payload": build_order_payload(order, items_payload)
        }],
        queue="notification_queue"
    )

    return attach_order_details(db, order)
