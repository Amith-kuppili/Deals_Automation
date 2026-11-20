import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from src.providers.ecommerce.client import ECommerceClient
from src.providers.ecommerce.exceptions import ECommerceAuthenticationError, ECommerceRateLimitError

@pytest.fixture
def client():
    return ECommerceClient()

@pytest.mark.asyncio
async def test_request_authentication_error(client):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response
        
        with pytest.raises(ECommerceAuthenticationError):
            await client._request("GET", "/test")

@pytest.mark.asyncio
async def test_request_rate_limit_retry(client):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        # First response is 429, second is 200
        res429 = MagicMock()
        res429.status_code = 429
        
        res200 = MagicMock()
        res200.status_code = 200
        res200.json.return_value = {"status": "ok"}
        
        mock_request.side_effect = [res429, res200]
        
        result = await client._request("GET", "/test")
        assert result == {"status": "ok"}
        assert mock_request.call_count == 2
