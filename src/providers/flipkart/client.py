import httpx
import logging
import asyncio
from typing import Any, Dict, Optional, List
from src.config.settings import settings
from src.providers.flipkart.exceptions import (
    FlipkartAPIError, 
    FlipkartAuthenticationError, 
    FlipkartRateLimitError,
    FlipkartError
)

logger = logging.getLogger(__name__)

class FlipkartClient:
    """
    Low-level client to interact with the official Flipkart Affiliate API.
    Handles authentication, rate limiting, and retries.
    """
    def __init__(self):
        self.base_url = "https://affiliate-api.flipkart.net/affiliate"
        self.api_token = settings.FLIPKART_API_TOKEN
        self.tracking_id = settings.FLIPKART_TRACKING_ID
        self.timeout = settings.FLIPKART_TIMEOUT_SECONDS
        self.max_retries = settings.FLIPKART_MAX_RETRIES

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Fk-Affiliate-Id": self.tracking_id,
            "Fk-Affiliate-Token": self.api_token,
            "Accept": "application/json"
        }

    async def request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform an HTTP request with retries and error handling.
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method, 
                        url, 
                        headers=self._get_headers(), 
                        params=params
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    
                    if response.status_code == 401:
                        raise FlipkartAuthenticationError("Invalid API credentials", 401, response.text)
                    
                    if response.status_code == 429:
                        if attempt < self.max_retries - 1:
                            wait_time = (2 ** attempt) + 1
                            logger.warning(f"Rate limit hit. Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        raise FlipkartRateLimitError("API rate limit exceeded", 429, response.text)
                    
                    if 500 <= response.status_code < 600:
                        if attempt < self.max_retries - 1:
                            wait_time = (2 ** attempt) + 1
                            logger.warning(f"Server error {response.status_code}. Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        raise FlipkartAPIError("Flipkart server error", response.status_code, response.text)
                    
                    raise FlipkartAPIError("Unexpected API response", response.status_code, response.text)

            except httpx.RequestError as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise FlipkartError(f"HTTP request failed: {str(e)}")

        raise FlipkartError("Maximum retries exceeded")

    async def get_category_list(self) -> List[Dict[str, Any]]:
        """Fetch the list of available categories in the product feed."""
        # Endpoint based on documentation: GET /feeds/{trackingId}/category/{format}
        # Actually, Product Feed Listing API provides the categories.
        endpoint = f"/feeds/{self.tracking_id}/category.json"
        return await self.request("GET", endpoint)

    async def get_product_feed(self, category: str) -> Dict[str, Any]:
        """Fetch all products for a specific category."""
        endpoint = f"/feeds/{self.tracking_id}/category/{category}.json"
        return await self.request("GET", endpoint)

    async def get_delta_feed(self, category: str, from_version: Optional[str] = None) -> Dict[str, Any]:
        """Fetch updated products for a specific category."""
        endpoint = f"/deltaFeeds/{self.tracking_id}/category/{category}.json"
        params = {}
        if from_version:
            params["fromVersion"] = from_version
        return await self.request("GET", endpoint, params=params)

    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Fetch details for a specific product ID."""
        endpoint = f"/product.json"
        params = {"productId": product_id}
        return await self.request("GET", endpoint, params=params)

    async def search_products(self, query: str) -> Dict[str, Any]:
        """Search for products based on keywords."""
        endpoint = f"/search.json"
        params = {"keyword": query}
        return await self.request("GET", endpoint, params=params)
