import logging
from typing import List, Optional
from src.providers.base import ProductProvider, ProductData
from src.providers.ecommerce.amazon.openwebninja_provider import OpenWebNinjaProvider
from src.providers.ecommerce.amazon.brightdata_provider import BrightDataProvider
from src.providers.ecommerce.amazon.exceptions import (
    AmazonAuthenticationError,
    AmazonRateLimitError,
    AmazonQuotaExceededError,
    AmazonTimeoutError,
    AmazonUnavailableError,
    AmazonProviderError
)
from src.config.settings import settings
from src.providers.ecommerce.amazon.quota_protection import quota_manager

logger = logging.getLogger(__name__)


class AmazonProviderManager:
    """
    Manages Amazon product collection with primary and backup provider failover.
    """
    def __init__(self):
        self.providers = {
            "openwebninja": OpenWebNinjaProvider() if settings.OPENWEBNINJA_ENABLED else None,
            "brightdata": BrightDataProvider() if settings.BRIGHTDATA_ENABLED else None,
        }
        self.primary_key = settings.AMAZON_PRIMARY_PROVIDER
        self.backup_key = settings.AMAZON_BACKUP_PROVIDER

    @property
    def primary_provider(self) -> Optional[ProductProvider]:
        return self._get_provider(self.primary_key)

    @primary_provider.setter
    def primary_provider(self, provider: Optional[ProductProvider]) -> None:
        self.providers[self.primary_key] = provider

    @property
    def backup_provider(self) -> Optional[ProductProvider]:
        return self._get_provider(self.backup_key)

    @backup_provider.setter
    def backup_provider(self, provider: Optional[ProductProvider]) -> None:
        self.providers[self.backup_key] = provider

    def _get_provider(self, key: str) -> Optional[ProductProvider]:
        return self.providers.get(key)

    def _is_failover_error(self, e: Exception) -> bool:
        """
        Determines if an exception should trigger failover to the backup provider.
        """
        # Failover on provider-level failures
        if isinstance(e, (
            AmazonAuthenticationError,
            AmazonRateLimitError,
            AmazonQuotaExceededError,
            AmazonTimeoutError,
            AmazonUnavailableError
        )):
            return True

        # Also failover on generic AmazonProviderError if it's not a validation error
        if isinstance(e, AmazonProviderError):
            return True

        return False

    async def search_products(self, query: str, platform: str) -> List[ProductData]:
        # 1. Try Primary
        primary = self._get_provider(self.primary_key)
        if primary:
            try:
                # Quota Protection for OpenWeb Ninja
                if self.primary_key == "openwebninja":
                    quota_manager.check_quota("openwebninja", settings.OPENWEBNINJA_MONTHLY_REQUEST_LIMIT)
                    quota_manager.increment_request("openwebninja")

                return await primary.search_products(query, platform)
            except Exception as e:
                if self._is_failover_error(e):
                    logger.warning(f"Primary Amazon provider {self.primary_key} failed: {str(e)}. Falling back to backup.")
                else:
                    logger.error(f"Non-failover error in primary Amazon provider {self.primary_key}: {str(e)}")
                    raise

        # 2. Try Backup
        backup = self._get_provider(self.backup_key)
        if backup:
            try:
                return await backup.search_products(query, platform)
            except Exception as e:
                logger.error(f"Backup Amazon provider {self.backup_key} also failed: {str(e)}")
                raise

        logger.error("No Amazon providers available.")
        return []

    async def get_product(self, product_id: str, platform: str) -> Optional[ProductData]:
        # 1. Try Primary
        primary = self._get_provider(self.primary_key)
        if primary:
            try:
                # Quota Protection for OpenWeb Ninja
                if self.primary_key == "openwebninja":
                    quota_manager.check_quota("openwebninja", settings.OPENWEBNINJA_MONTHLY_REQUEST_LIMIT)
                    quota_manager.increment_request("openwebninja")

                return await primary.get_product(product_id, platform)
            except Exception as e:
                if self._is_failover_error(e):
                    logger.warning(f"Primary Amazon provider {self.primary_key} failed for product {product_id}: {str(e)}. Falling back to backup.")
                else:
                    logger.error(f"Non-failover error in primary Amazon provider {self.primary_key}: {str(e)}")
                    raise

        # 2. Try Backup
        backup = self._get_provider(self.backup_key)
        if backup:
            try:
                return await backup.get_product(product_id, platform)
            except Exception as e:
                logger.error(f"Backup Amazon provider {self.backup_key} also failed for product {product_id}: {str(e)}")
                raise

        logger.error("No Amazon providers available for product details.")
        return None

    async def get_price(self, product_id: str, platform: str) -> Optional[float]:
        product = await self.get_product(product_id, platform)
        return product.current_price if product else None

    async def get_updates(self) -> List[ProductData]:
        # Aggregate updates from both if needed, or just primary
        results = []
        for key in [self.primary_key, self.backup_key]:
            provider = self._get_provider(key)
            if provider:
                results.extend(await provider.get_updates())
        return results
