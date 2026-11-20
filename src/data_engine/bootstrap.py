import logging
from datetime import datetime, timezone
from typing import List, Optional
from src.providers.reefapi.provider import ReefAPIProvider
from src.providers.base import ProductData
from src.config.settings import settings
from src.database.session import AsyncSessionLocal
from src.database.models import PriceHistory, Product
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

class ReefAPIBootstrapManager:
    """
    Handles bootstrapping product history using ReefAPI when local history is insufficient.
    """
    def __init__(self):
        self.provider = ReefAPIProvider()

    async def bootstrap_product(self, product: Product) -> int:
        """
        Fetches historical data from ReefAPI and stores it in PriceHistory.
        Returns the number of new observations imported.
        """
        if not settings.REEFAPI_ENABLED or not settings.REEFAPI_BOOTSTRAP_ENABLED:
            logger.info(f"ReefAPI bootstrap disabled for product {product.id}")
            return 0

        # Cooldown check: avoid bootstrapping the same product too frequently
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PriceHistory.recorded_at)
                .where(PriceHistory.product_id == product.id, PriceHistory.source == "reefapi")
                .order_by(PriceHistory.recorded_at.desc())
                .limit(1)
            )
            last_bootstrap = result.scalar()
            if last_bootstrap:
                cooldown_delta = datetime.now(timezone.utc) - last_bootstrap
                if cooldown_delta.total_seconds() < settings.REEFAPI_BOOTSTRAP_COOLDOWN_HOURS * 3600:
                    logger.info(f"ReefAPI bootstrap in cooldown for product {product.id}")
                    return 0

        logger.info(f"Attempting ReefAPI bootstrap for product {product.source_product_id} ({product.platform})")
        
        try:
            observations = await self.provider.get_historical_observations(
                product.source_product_id, 
                product.platform
            )
            
            if not observations:
                logger.info(f"No historical data found in ReefAPI for product {product.source_product_id}")
                return 0

            async with AsyncSessionLocal() as session:
                imported_count = 0
                for obs in observations:
                    # Deduplication: Check if an observation with the same price already exists
                    # for this product. In a real API, we would check the timestamp.
                    exists_result = await session.execute(
                        select(PriceHistory.id)
                        .where(
                            PriceHistory.product_id == product.id,
                            PriceHistory.price == obs.current_price,
                            PriceHistory.source == "reefapi"
                        )
                        .limit(1)
                    )
                    if exists_result.scalar():
                        continue

                    price_entry = PriceHistory(
                        product_id=product.id,
                        price=obs.current_price,
                        listed_price=obs.listed_price,
                        seller=obs.seller,
                        availability="available" if obs.availability else "unavailable",
                        source="reefapi"
                    )
                    session.add(price_entry)
                    imported_count += 1
                
                await session.commit()
                logger.info(f"ReefAPI bootstrap completed for {product.source_product_id}. Imported {imported_count} observations.")
                return imported_count

        except Exception as e:
            logger.error(f"Unexpected error during ReefAPI bootstrap for {product.source_product_id}: {str(e)}")
            return 0
