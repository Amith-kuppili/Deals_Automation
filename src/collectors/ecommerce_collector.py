import logging
import asyncio
from typing import List, Optional, Dict, Any
from src.providers.ecommerce.provider import ECommerceProvider
from src.providers.ecommerce.amazon.provider_manager import AmazonProviderManager
from src.providers.base import ProductData
from src.config.settings import settings
from src.workers.tasks import process_product_update
from src.providers.ecommerce.exceptions import ECommerceCreditLimitError

logger = logging.getLogger(__name__)

class ECommerceCollector:
    """
    Collector for E-Commerce products using a two-stage discovery process:
    Search -> Filter -> Item Verification.
    """
    def __init__(self):
        self.generic_provider = ECommerceProvider()
        self.amazon_manager = AmazonProviderManager()

    async def _get_provider(self, platform: str):
        """
        Returns the appropriate provider based on the platform.
        """
        if platform == "amazon":
            return self.amazon_manager
        return self.generic_provider

    async def check_credits(self, platform: str) -> int:
        """
        Checks current API credit balance.
        """
        try:
            if platform == "amazon":
                # Amazon providers might have different credit check mechanisms
                # For now, return a high value or implement specific checks
                return 100 
            
            credits = await self.generic_provider.client.get_credits()
            return credits.credits_remaining
        except Exception as e:
            logger.error(f"Failed to check API credits for {platform}: {str(e)}")
            return 0

    def _should_proceed(self, credits: int, platform: str, mode: str = "full") -> bool:
        """
        Credit-aware safety mechanism.
        """
        if platform == "amazon":
            return True # Amazon quota is handled by ProviderManager/QuotaProtection

        min_credits = settings.ECOMMERCE_API_MIN_CREDITS
        low_threshold = settings.ECOMMERCE_API_LOW_CREDITS_THRESHOLD

        if credits < min_credits:
            logger.error(f"Critical credit level ({credits}). Disabling provider.")
            return False
        
        if mode == "verification" and credits < min_credits:
            return False

        return True

    async def collect(self, platform: str, query: str, max_candidates: int = 5):
        """
        Executes the discovery pipeline.
        """
        logger.info(f"Starting E-Commerce collection for {platform}: {query}")

        # 1. Credit Check
        credits = await self.check_credits(platform)
        if not self._should_proceed(credits, platform):
            return {"status": "skipped", "reason": "insufficient_credits", "credits": credits}

        # 2. Stage 1: Search
        try:
            provider = await self._get_provider(platform)
            products = await provider.search_products(query, platform)
        except Exception as e:
            logger.error(f"Search failed for {platform}: {str(e)}")
            return {"status": "error", "reason": str(e)}

        if not products:
            logger.info(f"No products found in search for {platform}.")
            return {"status": "success", "found": 0}

        # 3. Cheap Filtering
        candidates = products[:max_candidates]
        logger.info(f"Found {len(products)} items, selected {len(candidates)} for verification.")

        # 4. Stage 2: Item Verification (Expensive Calls)
        if platform != "amazon" and credits < settings.ECOMMERCE_API_LOW_CREDITS_THRESHOLD:
            logger.warning("Low credit balance. Reducing candidate count.")
            candidates = candidates[:2]

        verified_count = 0
        provider = await self._get_provider(platform)
        for candidate in candidates:
            try:
                # Get detailed information
                detailed_product = await provider.get_product(
                    candidate.source_product_id, 
                    platform
                )
                
                if detailed_product:
                    # Dispatch to Celery worker for DB persistence
                    process_product_update.delay(detailed_product.model_dump())
                    verified_count += 1
            except Exception as e:
                logger.error(f"Verification failed for {candidate.source_product_id}: {str(e)}")

        return {
            "status": "success",
            "search_results": len(products),
            "verified": verified_count,
            "credits_remaining": await self.check_credits(platform)
        }
