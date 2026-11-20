import logging
import asyncio
from src.config.settings import settings
from src.providers.ecommerce.amazon.exceptions import AmazonQuotaExceededError

logger = logging.getLogger(__name__)

class QuotaManager:
    """
    Tracks and protects API quotas for providers.
    """
    def __init__(self):
        # In a production environment, this should be backed by Redis
        # For this implementation, we use an in-memory counter
        self._request_counts = {}

    def increment_request(self, provider: str):
        if provider not in self._request_counts:
            self._request_counts[provider] = 0
        self._request_counts[provider] += 1
        return self._request_counts[provider]

    def get_usage(self, provider: str) -> int:
        return self._request_counts.get(provider, 0)

    def check_quota(self, provider: str, limit: int):
        usage = self.get_usage(provider)
        if usage >= limit:
            logger.error(f"Quota exceeded for {provider}: {usage}/{limit}")
            raise AmazonQuotaExceededError(f"Monthly request limit of {limit} reached for {provider}")

# Singleton instance
quota_manager = QuotaManager()
