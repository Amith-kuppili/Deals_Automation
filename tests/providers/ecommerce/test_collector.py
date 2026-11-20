import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.collectors.ecommerce_collector import ECommerceCollector
from src.providers.ecommerce.models import SearchResponse, SearchItemResponse, ItemResponse, CreditResponse

@pytest.fixture
def collector():
    return ECommerceCollector()

@pytest.mark.asyncio
async def test_two_stage_pipeline(collector):
    # Mock search results
    mock_search_item = SearchItemResponse(
        id="ITEM1", title="T1", price=100.0, mrp=200.0, url="u1", availability=True
    )
    mock_search_res = SearchResponse(
        total=1, items=[mock_search_item], page=1, limit=20
    )
    
    # Mock detailed item result
    mock_item_res = ItemResponse(
        id="ITEM1", title="T1", price=100.0, mrp=200.0, url="u1", availability=True
    )
    
    # Mock credits
    mock_credits = CreditResponse(credits_remaining=100)

    with patch.object(collector.generic_provider.client, 'get_credits', new_callable=AsyncMock) as mock_get_credits, \
         patch.object(collector.generic_provider, 'search_products', new_callable=AsyncMock) as mock_search, \
         patch.object(collector.generic_provider, 'get_product', new_callable=AsyncMock) as mock_get_prod, \
         patch("src.collectors.ecommerce_collector.process_product_update.delay") as mock_delay:
        
        mock_get_credits.return_value = mock_credits
        mock_search.return_value = [collector.generic_provider._normalize_search_item(mock_search_item, "flipkart")]
        mock_get_prod.return_value = collector.generic_provider._normalize_item_detail(mock_item_res, "flipkart")
        
        result = await collector.collect("flipkart", "test")
        
        assert result["status"] == "success"
        assert result["verified"] == 1
        mock_delay.assert_called_once()

@pytest.mark.asyncio
async def test_credit_protection_disabled(collector):
    mock_credits = CreditResponse(credits_remaining=2) # below min_credits=5
    
    with patch.object(collector.generic_provider.client, 'get_credits', new_callable=AsyncMock) as mock_get_credits:
        mock_get_credits.return_value = mock_credits
        
        result = await collector.collect("flipkart", "test")
        
        assert result["status"] == "skipped"
        assert result["reason"] == "insufficient_credits"
