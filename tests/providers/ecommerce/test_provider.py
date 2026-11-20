import pytest
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from src.providers.ecommerce.provider import ECommerceProvider
from src.providers.ecommerce.client import ECommerceClient
from src.providers.ecommerce.models import SearchResponse, ItemResponse
from src.providers.ecommerce.exceptions import ECommerceAuthenticationError, ECommerceRateLimitError

@pytest.fixture
def provider():
    return ECommerceProvider()

@pytest.fixture
def mock_search_data():
    with open(os.path.join("tests", "fixtures", "ecommerce", "search.json")) as f:
        return json.load(f)

@pytest.fixture
def mock_item_data():
    with open(os.path.join("tests", "fixtures", "ecommerce", "item.json")) as f:
        return json.load(f)

@pytest.mark.asyncio
async def test_search_normalization(provider, mock_search_data):
    # Mock the client's search method
    provider.client.search = AsyncMock(return_value=SearchResponse(**mock_search_data))
    
    results = await provider.search_products("test", "flipkart")
    
    assert len(results) == 2
    assert results[0].source == "quickcommerce"
    assert results[0].platform == "flipkart"
    assert results[0].title == "Wireless Earbuds Pro"
    assert results[0].current_price == 2999.0

@pytest.mark.asyncio
async def test_item_normalization(provider, mock_item_data):
    # Mock the client's get_item method
    provider.client.get_item = AsyncMock(return_value=ItemResponse(**mock_item_data))
    
    product = await provider.get_product("ITEM1", "flipkart")
    
    assert product is not None
    assert product.brand == "AudioTech"
    assert product.sku == "SKU123"
    assert product.current_price == 2999.0

@pytest.mark.asyncio
async def test_get_price(provider, mock_item_data):
    provider.client.get_item = AsyncMock(return_value=ItemResponse(**mock_item_data))
    
    price = await provider.get_price("ITEM1", "flipkart")
    assert price == 2999.0
