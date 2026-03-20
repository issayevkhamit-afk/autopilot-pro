"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shops",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, server_default="Мой автосервис"),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
        sa.Column("logo_path", sa.String(500)),
        sa.Column("city", sa.String(100)),
        sa.Column("phone", sa.String(50)),
        sa.Column("language", sa.String(5), server_default="ru"),
        sa.Column("currency", sa.String(10), server_default="KZT"),
        sa.Column("address", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_shops_slug", "shops", ["slug"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=False),
        sa.Column("username", sa.String(100)),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("language", sa.String(5), server_default="ru"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), server_default="worker"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "shop_id", name="uq_user_shop"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("plan", sa.String(30), server_default="trial"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("trial_ends_at", sa.DateTime),
        sa.Column("expires_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "labor_prices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(30), server_default="flat"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_labor_prices_shop_id", "labor_prices", ["shop_id"])

    op.create_table(
        "part_prices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("brand", sa.String(100)),
        sa.Column("part_number", sa.String(100)),
        sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(30), server_default="pcs"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_part_prices_shop_id", "part_prices", ["shop_id"])

    op.create_table(
        "estimates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("car_make", sa.String(100)),
        sa.Column("car_model", sa.String(100)),
        sa.Column("car_year", sa.String(10)),
        sa.Column("car_vin", sa.String(50)),
        sa.Column("raw_input", sa.Text),
        sa.Column("total_labor", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_parts", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total", sa.Numeric(12, 2), server_default="0"),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("pdf_path", sa.String(500)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_estimates_shop_id", "estimates", ["shop_id"])

    op.create_table(
        "estimate_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("estimate_id", sa.Integer, sa.ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("qty", sa.Numeric(8, 2), server_default="1"),
        sa.Column("unit_price", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_price", sa.Numeric(12, 2), server_default="0"),
        sa.Column("is_manual", sa.String(5), server_default="false"),
    )
    op.create_index("ix_estimate_items_estimate_id", "estimate_items", ["estimate_id"])


def downgrade() -> None:
    op.drop_table("estimate_items")
    op.drop_table("estimates")
    op.drop_table("part_prices")
    op.drop_table("labor_prices")
    op.drop_table("subscriptions")
    op.drop_table("memberships")
    op.drop_table("users")
    op.drop_table("shops")
