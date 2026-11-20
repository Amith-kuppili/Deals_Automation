import pytest
import json
import os
from unittest.mock import AsyncMock, MagicMock
from src.providers.flipkart.provider import FlipkartProvider
from src.providers.flipkart.exceptions import FlipkartNormalizationError

@pytest.fixture
def provider():
    return FlipkartProvider()

@pytest.fixture
def mock_feed():
    fixture_path = os.path.join("tests", "fixtures", "flipkart", "product_feed.json")
    with open(fixture_path, "r") as f:
        return json.load(f)

@pytest.mark.asyncio
async def test_normalize_product_success(provider, mock_feed):
    # Test normalization of a valid product
    product_raw = mock_feed["products"][0]
    product_data = provider._normalize_product(product_raw)
    
    assert product_data.source == "flipkart"
    assert product_data.source_product_id == "PROD123"
    assert product_data.title == "Apple iPhone 15 (Black, 128 GB)"
    assert product_data.current_price == 69999.0
    assert product_data.listed_price == 79900.0

@pytest.mark.asyncio
async def test_normalize_product_invalid_data(provider):
    # Test normalization with missing fields
    invalid_product = {"productId": "INVALID"}
    
    # Based on provider.py, it uses .get() but might fail on float conversion if None
    # Let's see if it raises FlipkartNormalizationError
    with pytest.raises(FlipkartNormalizationError):
        provider._normalize_product(invalid_product)

@pytest.mark.asyncio
async def test_search_products(provider, mock_feed):
    # Mock the client's search_products method
    provider.client.search_products = AsyncMock(return_value={"products": mock_feed["products"]})
    
    results = await provider.search_products("iphone")
    
    assert len(results) == 3
    assert results[0].source_product_id == "PROD123"

@pytest.mark.asyncio
async def test_get_product(provider, mock_feed):
    # Mock the client's get_product_details method
    product_raw = mock_feed["products"][0]
    provider.client.get_product_details = AsyncMock(return_value=product_raw)
    
    product = await provider.get_product("PROD123")
    
    assert product is not None
    assert product.source_product_id == "PROD123"

@pytest.mark.asyncio
async def test_get_product_not_found(provider):
    # Mock the client to return None or empty
    provider.client.get_product_details = AsyncMock(return_value=None)
    
    product = await provider.get_product("UNKNOWN")
    
    assert product is None
