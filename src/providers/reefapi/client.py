import httpx
import logging
import asyncio
from typing import Any, Dict, Optional
from src.config.settings import settings
from src.providers.reefapi.exceptions import (
    ReefAPIError,
    ReefAPIAuthenticationError,
    ReefAPIRateLimitError,
    ReefAPIQuotaError,
    ReefAPITimeoutError,
    ReefAPIInvalidResponseError
)
from src.providers.reefapi.models import ReefAPIHistoryResponse

logger = logging.getLogger(__name__)

class ReefAPIClient:
    """
    Low-level HTTP client for ReefAPI.
    """
    def __init__(self):
        self.base_url = settings.REEFAPI_BASE_URL
        self.api_key = settings.REEFAPI_API_KEY
        self.timeout = settings.REEFAPI_TIMEOUT_SECONDS
        self.max_retries = settings.REEFAPI_MAX_RETRIES

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
                        raise ReefAPIAuthenticationError(f"Authentication failed: {response.text}")
                    
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) + 0.1
                        logger.warning(f"ReefAPI rate limit exceeded. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    if response.status_code == 402:
                        raise ReefAPIQuotaError(f"ReefAPI quota exhausted: {response.text}")
                    
                    if 500 <= response.status_code < 600:
                        wait_time = (2 ** attempt)
                        logger.warning(f"ReefAPI server error {response.status_code}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    raise ReefAPIError(f"ReefAPI request failed with status {response.status_code}: {response.text}")

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise ReefAPITimeoutError(f"ReefAPI request timed out after {self.max_retries} attempts")
                await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                raise ReefAPIError(f"Network error occurred: {str(e)}")

        raise ReefAPIError("Maximum retries exceeded for ReefAPI")

    async def get_historical_data(self, product_id: str, platform: str) -> ReefAPIHistoryResponse:
        params = {"product_id": product_id, "platform": platform}
        data = await self._request("GET", "/history", params=params)
        try:
            return ReefAPIHistoryResponse(**data)
        except Exception as e:
            raise ReefAPIInvalidResponseError(f"Failed to parse ReefAPI history response: {str(e)}")
