"""order item inventory snapshot

Revision ID: 20260506_order_0003
Revises: 20260506_order_0002
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260506_order_0003"
down_revision = "20260506_order_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("order_items", sa.Column("product_id", sa.Integer(), nullable=True))
    op.add_column("order_items", sa.Column("sku", sa.String(length=80), nullable=True))
    op.add_column("order_items", sa.Column("hsn_sac_code", sa.String(length=20), nullable=True))
    op.add_column("order_items", sa.Column("unit_of_measure", sa.String(length=30), nullable=True))
    op.add_column("order_items", sa.Column("tax_rate", sa.Numeric(5, 2), nullable=True))


def downgrade():
    op.drop_column("order_items", "tax_rate")
    op.drop_column("order_items", "unit_of_measure")
    op.drop_column("order_items", "hsn_sac_code")
    op.drop_column("order_items", "sku")
    op.drop_column("order_items", "product_id")
