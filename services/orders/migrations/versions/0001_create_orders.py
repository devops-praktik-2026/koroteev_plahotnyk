"""Создание таблицы заказов."""

import sqlalchemy as sa
from alembic import op

revision = "orders_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("item", sa.String(200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("quantity >= 1", name="positive_quantity"),
        sa.CheckConstraint("account_id >= 1", name="positive_account_id"),
    )
    op.create_index("ix_orders_account_id", "orders", ["account_id"])


def downgrade():
    op.drop_index("ix_orders_account_id", table_name="orders")
    op.drop_table("orders")
