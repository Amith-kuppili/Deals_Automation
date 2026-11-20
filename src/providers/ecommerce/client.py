import httpx
import logging
import asyncio
from typing import Any, Dict, Optional
from src.config.settings import settings
from src.providers.ecommerce.exceptions import (
    ECommerceAPIError,
    ECommerceAuthenticationError,
    ECommerceRateLimitError,
    ECommerceTimeoutError,
    ECommerceInvalidResponseError,
    ECommerceCreditLimitError
)
from src.providers.ecommerce.models import (
    SearchResponse,
    ItemResponse,
    CreditResponse
)

logger = logging.getLogger(__name__)

class ECommerceClient:
    """
    Low-level HTTP client for QuickCommerce API.
    Responsible only for communication and raw response retrieval.
    """
    def __init__(self):
        self.base_url = settings.ECOMMERCE_API_BASE_URL
        self.api_key = settings.ECOMMERCE_API_KEY
        self.timeout = settings.ECOMMERCE_API_TIMEOUT_SECONDS
        self.max_retries = settings.ECOMMERCE_API_MAX_RETRIES

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, headers=headers, params=params, json=data)
                    
                    if response.status_code == 200:
                        return response.json()
                    
                    if response.status_code in (401, 403):
                        raise ECommerceAuthenticationError(f"Authentication failed: {response.text}")
                    
                    if response.status_code == 429:
                        # Exponential backoff for rate limits
                        wait_time = (2 ** attempt) + (0.1 * attempt) # simple jitter
                        logger.warning(f"Rate limit exceeded. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    if response.status_code == 402: # Often used for Payment Required / Insufficient Credits
                        raise ECommerceCreditLimitError(f"Insufficient API credits: {response.text}")
                    
                    if 500 <= response.status_code < 600:
                        wait_time = (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    raise ECommerceAPIError(f"API request failed with status {response.status_code}: {response.text}")

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise ECommerceTimeoutError(f"API request timed out after {self.max_retries} attempts")
                await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                raise ECommerceAPIError(f"Network error occurred: {str(e)}")

        raise ECommerceAPIError("Maximum retries exceeded")

    async def search(self, platform: str, query: str, page: int = 1, limit: int = 20) -> SearchResponse:
        params = {
            "platform": platform,
            "query": query,
            "page": page,
            "limit": limit
        }
        data = await self._request("GET", "/search", params=params)
        try:
            return SearchResponse(**data)
        except Exception as e:
            raise ECommerceInvalidResponseError(f"Failed to parse search response: {str(e)}")

    async def get_item(self, platform: str, item_id: str) -> ItemResponse:
        params = {
            "platform": platform,
            "item_id": item_id
        }
        data = await self._request("GET", "/item", params=params)
        try:
            return ItemResponse(**data)
        except Exception as e:
            raise ECommerceInvalidResponseError(f"Failed to parse item response: {str(e)}")

    async def get_credits(self) -> CreditResponse:
        data = await self._request("GET", "/credits")
        try:
            return CreditResponse(**data)
        except Exception as e:
            raise ECommerceInvalidResponseError(f"Failed to parse credits response: {str(e)}")
