from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True) # e.g., 'flipkart', 'amazon'
    source = Column(String, index=True) # e.g., 'quickcommerce'
    source_product_id = Column(String, index=True)
    title = Column(String)
    normalized_title = Column(String, index=True)
    category = Column(String, index=True)
    brand = Column(String)
    url = Column(Text)
    image_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    prices = relationship("PriceHistory", back_populates="product")
    deal_scores = relationship("DealScore", back_populates="product")
    alert_history = relationship("AlertHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    price = Column(Float)
    listed_price = Column(Float)
    seller = Column(String)
    availability = Column(String)
    source = Column(String, index=True) # e.g., 'quickcommerce', 'openwebninja', 'reefapi'
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    product = relationship("Product", back_populates="prices")

class DealScore(Base):
    __tablename__ = "deal_scores"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    current_price = Column(Float)
    historical_median = Column(Float)
    historical_min = Column(Float)
    historical_max = Column(Float)
    displayed_discount = Column(Float)
    effective_discount = Column(Float)
    price_anomaly_score = Column(Float)
    confidence = Column(Float)
    classification = Column(String, index=True) # e.g., 'EXTREME_DEAL', 'FALSE_DISCOUNT'
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="deal_scores")
    alert_history = relationship("AlertHistory", back_populates="deal_score")


class AlertHistory(Base):
    __tablename__ = "alert_history"
    __table_args__ = (
        UniqueConstraint(
            "deal_score_id",
            "channel",
            name="uq_alert_history_deal_score_channel",
        ),
        Index(
            "ix_alert_history_product_created_at",
            "product_id",
            "created_at",
        ),
        Index(
            "ix_alert_history_channel_status_created_at",
            "channel",
            "status",
            "created_at",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deal_score_id = Column(
        Integer,
        ForeignKey("deal_scores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel = Column(String(32), nullable=False, default="telegram", index=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    message_id = Column(String(128))
    error_message = Column(Text)
    sent_at = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )

    product = relationship("Product", back_populates="alert_history")
    deal_score = relationship("DealScore", back_populates="alert_history")

class ProviderSyncState(Base):
    __tablename__ = "provider_sync_state"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True)
    category = Column(String, index=True)
    last_version = Column(String)
    last_success_at = Column(DateTime(timezone=True))
    last_error_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
