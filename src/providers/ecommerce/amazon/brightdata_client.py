import httpx
import logging
import asyncio
from typing import Any, Dict, Optional
from src.config.settings import settings
from src.providers.ecommerce.amazon.exceptions import (
    AmazonProviderError,
    AmazonAuthenticationError,
    AmazonRateLimitError,
    AmazonTimeoutError,
    AmazonInvalidResponseError,
    AmazonUnavailableError,
)

logger = logging.getLogger(__name__)


class BrightDataClient:
    """
    Low-level HTTP client for Bright Data API.
    """

    def __init__(self):
        self.base_url = settings.BRIGHTDATA_BASE_URL.rstrip("/")
        self.api_key = settings.BRIGHTDATA_API_KEY
        self.timeout = settings.BRIGHTDATA_TIMEOUT_SECONDS
        self.max_retries = settings.BRIGHTDATA_MAX_RETRIES

    def _client_config_error(self) -> Optional[str]:
        if not self.base_url:
            return "BRIGHTDATA_BASE_URL is not configured"
        if not self.api_key:
            return "BRIGHTDATA_API_KEY is not configured"
        return None

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        config_error = self._client_config_error()
        if config_error:
            raise AmazonUnavailableError(config_error)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, headers=headers, params=params, json=data)

                    if response.status_code == 200:
                        return response.json()

                    if response.status_code in (401, 403):
                        raise AmazonAuthenticationError(f"Bright Data authentication failed: {response.text[:200]}")

                    if response.status_code == 429:
                        wait_time = (2 ** attempt) + 0.1
                        logger.warning(f"Bright Data rate limit exceeded. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    if 500 <= response.status_code < 600:
                        wait_time = (2 ** attempt)
                        logger.warning(f"Bright Data server error {response.status_code}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    raise AmazonProviderError(
                        f"Bright Data API request failed with status {response.status_code}: {response.text[:200]}"
                    )

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise AmazonTimeoutError(f"Bright Data request timed out after {self.max_retries} attempts")
                await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                raise AmazonProviderError(f"Network error occurred: {str(e)}")

        raise AmazonProviderError("Maximum retries exceeded for Bright Data")

    async def search(self, query: str) -> Dict[str, Any]:
        params = {"query": query}
        return await self._request("GET", "/search", params=params)

    async def get_item(self, asin: str) -> Dict[str, Any]:
        params = {"asin": asin}
        return await self._request("GET", "/item", params=params)
