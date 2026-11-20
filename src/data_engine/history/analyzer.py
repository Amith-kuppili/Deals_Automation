import numpy as np
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import PriceHistory
from src.config.settings import settings

logger = logging.getLogger(__name__)

class HistoryStatistics:
    """
    Container for calculated historical price metrics.
    """
    def __init__(self, 
                 observation_count: int,
                 historical_min: float,
                 historical_max: float,
                 historical_median: float,
                 recent_median: float,
                 mad: float,
                 volatility: float):
        self.observation_count = observation_count
        self.historical_min = historical_min
        self.historical_max = historical_max
        self.historical_median = historical_median
        self.recent_median = recent_median
        self.mad = mad
        self.volatility = volatility

class HistoricalAnalyzer:
    """
    Analyzes PriceHistory to produce robust statistics and baselines.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_stats(self, product_id: int) -> Optional[HistoryStatistics]:
        # Fetch prices for the product within the configured window
        window_days = settings.DEAL_HISTORY_WINDOW_DAYS
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        result = await self.session.execute(
            select(PriceHistory.price)
            .where(
                PriceHistory.product_id == product_id,
                PriceHistory.recorded_at >= cutoff
            )
            .order_by(PriceHistory.recorded_at)
        )
        prices = result.scalars().all()
        
        if not prices:
            return None

        prices_arr = np.array(prices)
        count = len(prices_arr)
        
        # Robust statistics
        h_min = float(np.min(prices_arr))
        h_max = float(np.max(prices_arr))
        h_median = float(np.median(prices_arr))
        
        # Recent median (last 30 days or last N observations)
        # For simplicity, we take the last 30 observations as 'recent' if available
        recent_prices = prices_arr[-30:]
        recent_median = float(np.median(recent_prices))
        
        # Median Absolute Deviation (MAD) for robust anomaly detection
        median = np.median(prices_arr)
        mad = float(np.median(np.abs(prices_arr - median)))
        
        # Volatility (Coefficient of Variation)
        std = np.std(prices_arr)
        volatility = float(std / h_median) if h_median != 0 else 0.0
        
        return HistoryStatistics(
            observation_count=count,
            historical_min=h_min,
            historical_max=h_max,
            historical_median=h_median,
            recent_median=recent_median,
            mad=mad,
            volatility=volatility
        )

    async def get_robust_baseline(self, stats: HistoryStatistics) -> float:
        """
        Determines the most reliable baseline price.
        Priority: 30-day median -> 14-day median -> 7-day median -> historical median.
        """
        # In this implementation, we use the historical median as the primary baseline
        # but we could refine this by querying specific time windows from the DB.
        return stats.historical_median
