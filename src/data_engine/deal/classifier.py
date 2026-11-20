import logging
from typing import Tuple, Optional
from src.data_engine.history.analyzer import HistoryStatistics
from src.config.settings import settings

logger = logging.getLogger(__name__)

class DealClassifier:
    """
    Classifies products based on genuine discount rules.
    """
    def __init__(self):
        self.extreme_threshold = 0.90 # 90% genuine discount
        self.good_threshold = 0.30     # 30% genuine discount
        self.watch_threshold = 0.15    # 15% genuine discount

    def classify(self, current_price: float, baseline: float, stats: HistoryStatistics) -> Tuple[str, float, str]:
        """
        Classifies the deal and provides a reason.
        """
        if baseline == 0:
            return "INSUFFICIENT_HISTORY", 0.0, "Baseline price is zero."

        effective_discount = 1 - (current_price / baseline)
        
        # 1. Check for False Discount
        # If current price is very close to the historical median, it's a false discount
        # even if the marketplace claims 90% off.
        if effective_discount < 0.05 and stats.observation_count >= 5:
            # If the price is within 5% of the median, it's likely the normal price
            return "FALSE_DISCOUNT", effective_discount, f"Current price is only {effective_discount:.1%} below historical median."

        # 2. Extreme Deal
        if effective_discount >= self.extreme_threshold:
            # Require high confidence for extreme deals
            if stats.observation_count >= settings.DEAL_HIGH_CONFIDENCE_HISTORY_OBSERVATIONS:
                return "EXTREME_DEAL", effective_discount, f"Genuine extreme discount of {effective_discount:.1%} detected."
            else:
                return "GOOD_DEAL", effective_discount, f"Large discount of {effective_discount:.1%}, but history confidence is medium."

        # 3. Good Deal
        if effective_discount >= self.good_threshold:
            return "GOOD_DEAL", effective_discount, f"Meaningful discount of {effective_discount:.1%} detected."

        # 4. Watch
        if effective_discount >= self.watch_threshold:
            return "WATCH", effective_discount, f"Interesting price movement of {effective_discount:.1%}."

        return "NORMAL", effective_discount, "Price is within normal historical range."
