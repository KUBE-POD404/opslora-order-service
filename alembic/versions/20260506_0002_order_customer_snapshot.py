"""order customer snapshot

Revision ID: 20260506_order_0002
Revises: 20260501_order_0001
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260506_order_0002"
down_revision = "20260501_order_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("orders", sa.Column("customer_display_name", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("customer_phone", sa.String(length=50), nullable=True))
    op.add_column("orders", sa.Column("customer_type", sa.String(length=30), nullable=True))
    op.add_column("orders", sa.Column("customer_tax_id", sa.String(length=50), nullable=True))
    op.add_column("orders", sa.Column("customer_gstin", sa.String(length=20), nullable=True))
    op.add_column("orders", sa.Column("customer_tax_registration_type", sa.String(length=50), nullable=True))
    op.add_column("orders", sa.Column("customer_place_of_supply", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("billing_address_line1", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("billing_address_line2", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("billing_city", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("billing_state", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("billing_postal_code", sa.String(length=30), nullable=True))
    op.add_column("orders", sa.Column("billing_country", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("shipping_same_as_billing", sa.Boolean(), nullable=True))
    op.add_column("orders", sa.Column("shipping_address_line1", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("shipping_address_line2", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("shipping_city", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("shipping_state", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("shipping_postal_code", sa.String(length=30), nullable=True))
    op.add_column("orders", sa.Column("shipping_country", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("payment_terms_days", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("orders", "payment_terms_days")
    op.drop_column("orders", "shipping_country")
    op.drop_column("orders", "shipping_postal_code")
    op.drop_column("orders", "shipping_state")
    op.drop_column("orders", "shipping_city")
    op.drop_column("orders", "shipping_address_line2")
    op.drop_column("orders", "shipping_address_line1")
    op.drop_column("orders", "shipping_same_as_billing")
    op.drop_column("orders", "billing_country")
    op.drop_column("orders", "billing_postal_code")
    op.drop_column("orders", "billing_state")
    op.drop_column("orders", "billing_city")
    op.drop_column("orders", "billing_address_line2")
    op.drop_column("orders", "billing_address_line1")
    op.drop_column("orders", "customer_place_of_supply")
    op.drop_column("orders", "customer_tax_registration_type")
    op.drop_column("orders", "customer_gstin")
    op.drop_column("orders", "customer_tax_id")
    op.drop_column("orders", "customer_type")
    op.drop_column("orders", "customer_phone")
    op.drop_column("orders", "customer_display_name")
