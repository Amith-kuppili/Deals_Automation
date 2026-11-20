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
    AmazonQuotaExceededError,
    AmazonUnavailableError,
)
from src.providers.ecommerce.amazon.models import (
    OpenWebNinjaSearchResponse,
    OpenWebNinjaItemDetail,
)

logger = logging.getLogger(__name__)


class OpenWebNinjaClient:
    """
    Low-level HTTP client for the OpenWeb Ninja Real-Time Amazon Data API.

    Auth: `x-api-key` header.
    Endpoints: GET /search?query=..., GET /product-details?asin=...
    """

    def __init__(self):
        self.base_url = settings.OPENWEBNINJA_BASE_URL.rstrip("/")
        self.api_key = settings.OPENWEBNINJA_API_KEY
        self.country = settings.AMAZON_COUNTRY
        self.timeout = settings.OPENWEBNINJA_TIMEOUT_SECONDS
        self.max_retries = settings.OPENWEBNINJA_MAX_RETRIES

    def _client_config_error(self) -> Optional[str]:
        if not self.base_url:
            return "OPENWEBNINJA_BASE_URL is not configured"
        if not self.api_key:
            return "OPENWEBNINJA_API_KEY is not configured"
        return None

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        config_error = self._client_config_error()
        if config_error:
            raise AmazonUnavailableError(config_error)

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, headers=headers, params=params, json=data)

                    if response.status_code == 200:
                        payload = response.json()
                        status = str(payload.get("status", "OK")).upper()
                        if status not in ("OK", "SUCCESS"):
                            message = payload.get("error") or payload
                            raise AmazonProviderError(
                                f"OpenWeb Ninja returned status {status}: {str(message)[:200]}"
                            )
                        return payload

                    if response.status_code in (401, 403):
                        raise AmazonAuthenticationError(f"Authentication failed: {response.text}")

                    if response.status_code == 429:
                        wait_time = (2 ** attempt) + 0.1
                        logger.warning(f"OpenWeb Ninja rate limit exceeded. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status_code == 402:
                        raise AmazonQuotaExceededError(f"OpenWeb Ninja quota exhausted: {response.text}")

                    if 500 <= response.status_code < 600:
                        wait_time = (2 ** attempt)
                        logger.warning(f"OpenWeb Ninja server error {response.status_code}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    raise AmazonProviderError(
                        f"OpenWeb Ninja API request failed with status {response.status_code}: {response.text[:200]}"
                    )

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise AmazonTimeoutError(f"OpenWeb Ninja request timed out after {self.max_retries} attempts")
                await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                raise AmazonProviderError(f"Network error occurred: {str(e)}")

        raise AmazonProviderError("Maximum retries exceeded for OpenWeb Ninja")

    async def search(self, query: str) -> OpenWebNinjaSearchResponse:
        params = {"query": query, "country": self.country}
        data = await self._request("GET", "/search", params=params)
        try:
            return OpenWebNinjaSearchResponse(**data)
        except Exception as e:
            raise AmazonInvalidResponseError(f"Failed to parse OpenWeb Ninja search response: {str(e)}")

    async def get_item(self, asin: str) -> OpenWebNinjaItemDetail:
        params = {"asin": asin, "country": self.country}
        data = await self._request("GET", "/product-details", params=params)
        try:
            return OpenWebNinjaItemDetail(**data.get("data", {}))
        except Exception as e:
            raise AmazonInvalidResponseError(f"Failed to parse OpenWeb Ninja item response: {str(e)}")
