import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.data_engine.sufficiency import HistorySufficiencyEngine
from src.data_engine.deal.classifier import DealClassifier
from src.data_engine.history.analyzer import HistoricalAnalyzer, HistoryStatistics
from src.providers.reefapi.provider import ReefAPIProvider
from src.providers.base import ProductData

@pytest.mark.asyncio
async def test_sufficiency_engine():
    engine = HistorySufficiencyEngine()
    # New product
    assert engine.evaluate(0).status == "NEW_PRODUCT"
    # Insufficient
    assert engine.evaluate(3).status == "INSUFFICIENT_HISTORY"
    # Basic
    assert engine.evaluate(10).status == "BASIC_HISTORY"
    # High confidence
    assert engine.evaluate(25).status == "HIGH_CONFIDENCE_HISTORY"

@pytest.mark.asyncio
async def test_deal_classifier_genuine_extreme():
    classifier = DealClassifier()
    stats = HistoryStatistics(
        observation_count=30,
        historical_min=800,
        historical_max=1200,
        historical_median=1000,
        recent_median=1000,
        mad=50,
        volatility=0.05
    )
    # 91% discount
    classification, discount, reason = classifier.classify(90, 1000, stats)
    assert classification == "EXTREME_DEAL"
    assert discount == 0.91

@pytest.mark.asyncio
async def test_deal_classifier_false_discount():
    classifier = DealClassifier()
    stats = HistoryStatistics(
        observation_count=30,
        historical_min=950,
        historical_max=1050,
        historical_median=1000,
        recent_median=1000,
        mad=20,
        volatility=0.02
    )
    # Marketplace says 90% off (MRP 10000), but current is 990
    # Our baseline is 1000. Effective discount is only 1%.
    classification, discount, reason = classifier.classify(990, 1000, stats)
    assert classification == "FALSE_DISCOUNT"
    assert discount == pytest.approx(0.01)

@pytest.mark.asyncio
async def test_reefapi_provider_normalization():
    provider = ReefAPIProvider()
    mock_response = MagicMock()
    mock_response.history = [
        MagicMock(price=100.0, observed_at="2023-01-01", availability=True, seller="S1")
    ]
    
    with patch.object(provider.client, 'get_historical_data', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        results = await provider.get_historical_observations("B01", "amazon")
        assert len(results) == 1
        assert results[0].current_price == 100.0
        assert results[0].source == "reefapi"
