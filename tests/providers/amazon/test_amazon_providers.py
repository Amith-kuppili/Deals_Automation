import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.providers.ecommerce.amazon.openwebninja_provider import OpenWebNinjaProvider
from src.providers.ecommerce.amazon.brightdata_provider import BrightDataProvider
from src.providers.ecommerce.amazon.provider_manager import AmazonProviderManager
from src.providers.ecommerce.amazon.models import OpenWebNinjaSearchResponse
from src.providers.ecommerce.amazon.exceptions import (
    AmazonAuthenticationError,
    AmazonRateLimitError,
    AmazonQuotaExceededError,
    AmazonTimeoutError
)
from src.providers.base import ProductData

@pytest.mark.asyncio
async def test_openwebninja_search_success():
    provider = OpenWebNinjaProvider()
    mock_response = OpenWebNinjaSearchResponse(**{
        "status": "OK",
        "data": {
            "total_products": 1,
            "products": [
                {
                    "asin": "B01",
                    "product_title": "Product 1",
                    "product_price": "\u20b91,299",
                    "product_original_price": "\u20b91,999",
                    "currency": "INR",
                    "product_url": "url1",
                    "product_photo": "img1",
                    "category": {"id": "aps", "name": "cat1"},
                }
            ],
        },
    })

    with patch.object(provider.client, 'search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_response

        results = await provider.search_products("query", "amazon")
        assert len(results) == 1
        assert results[0].source_product_id == "B01"
        assert results[0].platform == "amazon"
        assert results[0].source == "openwebninja"
        assert results[0].title == "Product 1"
        assert results[0].current_price == 1299.0
        assert results[0].listed_price == 1999.0
        assert results[0].category == "cat1"
        assert results[0].currency == "INR"
        assert results[0].availability is True

@pytest.mark.asyncio
async def test_brightdata_search_success():
    provider = BrightDataProvider()
    mock_response = {
        "results": [
            {"asin": "B02", "title": "Product 2", "price": 200.0, "url": "url2", "image": "img2", "category": "cat2", "availability": True}
        ]
    }
    
    with patch.object(provider.client, 'search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_response
        
        results = await provider.search_products("query", "amazon")
        assert len(results) == 1
        assert results[0].source_product_id == "B02"
        assert results[0].source == "brightdata"

@pytest.mark.asyncio
async def test_amazon_manager_failover():
    manager = AmazonProviderManager()
    
    # Mock providers
    manager.primary_provider = AsyncMock()
    manager.backup_provider = AsyncMock()
    
    # Scenario 1: Primary Success
    manager.primary_provider.search_products.return_value = [ProductData(
        source="openwebninja", platform="amazon", source_product_id="B01", 
        title="P1", product_url="u1", current_price=10.0
    )]
    
    res = await manager.search_products("query", "amazon")
    assert res[0].source == "openwebninja"
    manager.backup_provider.search_products.assert_not_called()
    
    # Scenario 2: Primary Failover (Rate Limit)
    manager.primary_provider.search_products.side_effect = AmazonRateLimitError("Rate limit")
    manager.backup_provider.search_products.return_value = [ProductData(
        source="brightdata", platform="amazon", source_product_id="B01", 
        title="P1", product_url="u1", current_price=10.0
    )]
    
    res = await manager.search_products("query", "amazon")
    assert res[0].source == "brightdata"
    manager.backup_provider.search_products.assert_called_once()

@pytest.mark.asyncio
async def test_amazon_manager_no_failover_on_empty():
    manager = AmazonProviderManager()
    manager.primary_provider = AsyncMock()
    manager.backup_provider = AsyncMock()
    
    # Primary returns empty list (not an error)
    manager.primary_provider.search_products.return_value = []
    
    res = await manager.search_products("query", "amazon")
    assert res == []
    manager.backup_provider.search_products.assert_not_called()

@pytest.mark.asyncio
async def test_amazon_manager_quota_failover():
    manager = AmazonProviderManager()
    manager.primary_provider = AsyncMock()
    manager.backup_provider = AsyncMock()
    
    # Primary raises QuotaExceeded
    manager.primary_provider.search_products.side_effect = AmazonQuotaExceededError("Quota")
    manager.backup_provider.search_products.return_value = [ProductData(
        source="brightdata", platform="amazon", source_product_id="B01", 
        title="P1", product_url="u1", current_price=10.0
    )]
    
    res = await manager.search_products("query", "amazon")
    assert res[0].source == "brightdata"
