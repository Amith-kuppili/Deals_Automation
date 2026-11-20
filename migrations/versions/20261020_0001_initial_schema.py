"""Create the current application schema.

Revision ID: 20261020_0001
Revises:
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261020_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("source_product_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("normalized_title", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index("ix_products_platform", "products", ["platform"], unique=False)
    op.create_index("ix_products_source", "products", ["source"], unique=False)
    op.create_index("ix_products_source_product_id", "products", ["source_product_id"], unique=False)
    op.create_index("ix_products_normalized_title", "products", ["normalized_title"], unique=False)
    op.create_index("ix_products_category", "products", ["category"], unique=False)

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("listed_price", sa.Float(), nullable=True),
        sa.Column("seller", sa.String(), nullable=True),
        sa.Column("availability", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_history_id", "price_history", ["id"], unique=False)
    op.create_index("ix_price_history_product_id", "price_history", ["product_id"], unique=False)
    op.create_index("ix_price_history_source", "price_history", ["source"], unique=False)
    op.create_index("ix_price_history_recorded_at", "price_history", ["recorded_at"], unique=False)

    op.create_table(
        "deal_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("current_price", sa.Float(), nullable=True),
        sa.Column("historical_median", sa.Float(), nullable=True),
        sa.Column("historical_min", sa.Float(), nullable=True),
        sa.Column("historical_max", sa.Float(), nullable=True),
        sa.Column("displayed_discount", sa.Float(), nullable=True),
        sa.Column("effective_discount", sa.Float(), nullable=True),
        sa.Column("price_anomaly_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("classification", sa.String(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deal_scores_id", "deal_scores", ["id"], unique=False)
    op.create_index("ix_deal_scores_product_id", "deal_scores", ["product_id"], unique=False)
    op.create_index("ix_deal_scores_classification", "deal_scores", ["classification"], unique=False)

    op.create_table(
        "alert_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("deal_score_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message_id", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["deal_score_id"], ["deal_scores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deal_score_id", "channel", name="uq_alert_history_deal_score_channel"),
    )
    op.create_index("ix_alert_history_id", "alert_history", ["id"], unique=False)
    op.create_index("ix_alert_history_product_id", "alert_history", ["product_id"], unique=False)
    op.create_index("ix_alert_history_deal_score_id", "alert_history", ["deal_score_id"], unique=False)
    op.create_index("ix_alert_history_channel", "alert_history", ["channel"], unique=False)
    op.create_index("ix_alert_history_status", "alert_history", ["status"], unique=False)
    op.create_index("ix_alert_history_sent_at", "alert_history", ["sent_at"], unique=False)
    op.create_index("ix_alert_history_created_at", "alert_history", ["created_at"], unique=False)
    op.create_index(
        "ix_alert_history_product_created_at",
        "alert_history",
        ["product_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_alert_history_channel_status_created_at",
        "alert_history",
        ["channel", "status", "created_at"],
        unique=False,
    )

    op.create_table(
        "provider_sync_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("last_version", sa.String(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_sync_state_id", "provider_sync_state", ["id"], unique=False)
    op.create_index("ix_provider_sync_state_provider", "provider_sync_state", ["provider"], unique=False)
    op.create_index("ix_provider_sync_state_category", "provider_sync_state", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_provider_sync_state_category", table_name="provider_sync_state")
    op.drop_index("ix_provider_sync_state_provider", table_name="provider_sync_state")
    op.drop_index("ix_provider_sync_state_id", table_name="provider_sync_state")
    op.drop_table("provider_sync_state")

    op.drop_index("ix_alert_history_channel_status_created_at", table_name="alert_history")
    op.drop_index("ix_alert_history_product_created_at", table_name="alert_history")
    op.drop_index("ix_alert_history_created_at", table_name="alert_history")
    op.drop_index("ix_alert_history_sent_at", table_name="alert_history")
    op.drop_index("ix_alert_history_status", table_name="alert_history")
    op.drop_index("ix_alert_history_channel", table_name="alert_history")
    op.drop_index("ix_alert_history_deal_score_id", table_name="alert_history")
    op.drop_index("ix_alert_history_product_id", table_name="alert_history")
    op.drop_index("ix_alert_history_id", table_name="alert_history")
    op.drop_table("alert_history")

    op.drop_index("ix_deal_scores_classification", table_name="deal_scores")
    op.drop_index("ix_deal_scores_product_id", table_name="deal_scores")
    op.drop_index("ix_deal_scores_id", table_name="deal_scores")
    op.drop_table("deal_scores")

    op.drop_index("ix_price_history_recorded_at", table_name="price_history")
    op.drop_index("ix_price_history_source", table_name="price_history")
    op.drop_index("ix_price_history_product_id", table_name="price_history")
    op.drop_index("ix_price_history_id", table_name="price_history")
    op.drop_table("price_history")

    op.drop_index("ix_products_category", table_name="products")
    op.drop_index("ix_products_normalized_title", table_name="products")
    op.drop_index("ix_products_source_product_id", table_name="products")
    op.drop_index("ix_products_source", table_name="products")
    op.drop_index("ix_products_platform", table_name="products")
    op.drop_index("ix_products_id", table_name="products")
    op.drop_table("products")
