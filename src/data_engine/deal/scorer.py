import logging
from typing import Optional
from src.data_engine.history.analyzer import HistoricalAnalyzer, HistoryStatistics
from src.data_engine.deal.classifier import DealClassifier
from src.data_engine.sufficiency import HistorySufficiencyEngine
from src.database.models import DealScore, Product
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class DealScorer:
    """
    Orchestrates the deal scoring process.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analyzer = HistoricalAnalyzer(session)
        self.classifier = DealClassifier()

    async def score_product(self, product: Product, current_price: float) -> Optional[DealScore]:
        """
        Calculates the deal score for a product.
        """
        try:
            # 1. Analyze History
            stats = await self.analyzer.calculate_stats(product.id)
            if not stats:
                logger.info(f"No history for product {product.id}, skipping score.")
                return None

            # 2. Check Sufficiency
            sufficiency_engine = HistorySufficiencyEngine()
            sufficiency = sufficiency_engine.evaluate(stats.observation_count)
            
            if not sufficiency.is_sufficient:
                return DealScore(
                    product_id=product.id,
                    current_price=current_price,
                    historical_median=stats.historical_median,
                    historical_min=stats.historical_min,
                    historical_max=stats.historical_max,
                    effective_discount=0.0,
                    price_anomaly_score=0.0,
                    confidence=0.0,
                    classification="INSUFFICIENT_HISTORY",
                    reason=f"Only {stats.observation_count} observations found. Minimum {sufficiency_engine.min_observations} required."
                )

            # 3. Get Baseline
            baseline = await self.analyzer.get_robust_baseline(stats)
            
            # 4. Classify Deal
            classification, effective_discount, reason = self.classifier.classify(
                current_price, baseline, stats
            )
            
            # 5. Calculate Anomaly Score (Robust Z-Score)
            # z = 0.6745 * (x - median) / MAD
            anomaly_score = 0.0
            if stats.mad > 0:
                anomaly_score = 0.6745 * (current_price - stats.historical_median) / stats.mad
            
            # 6. Calculate Displayed Discount (Marketplace claim)
            # In a real scenario, this comes from the product_data.listed_price
            # For now, we estimate it as 1 - (current / listed) if listed exists
            displayed_discount = 0.0
            # Note: current_price is passed in, but listed_price is in the DB or product_data
            # We'll assume the caller provides the most recent listed_price via a separate mechanism 
            # or we fetch it from the last PriceHistory entry.
            
            # 7. Create DealScore object
            score_entry = DealScore(
                product_id=product.id,
                current_price=current_price,
                historical_median=stats.historical_median,
                historical_min=stats.historical_min,
                historical_max=stats.historical_max,
                displayed_discount=displayed_discount,
                effective_discount=effective_discount,
                price_anomaly_score=anomaly_score,
                confidence=min(1.0, stats.observation_count / 50.0), # Simple confidence metric
                classification=classification,
                reason=reason
            )
            
            return score_entry

        except Exception as e:
            logger.error(f"Error scoring product {product.id}: {str(e)}")
            return None
