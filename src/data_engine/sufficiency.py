import logging
from typing import Tuple
from src.config.settings import settings
from src.data_engine.models import HistorySufficiency

logger = logging.getLogger(__name__)

class HistorySufficiencyEngine:
    """
    Determines if a product has enough local price history for reliable deal scoring.
    """
    def __init__(self):
        self.min_observations = settings.DEAL_MIN_HISTORY_OBSERVATIONS
        self.high_confidence_observations = settings.DEAL_HIGH_CONFIDENCE_HISTORY_OBSERVATIONS
        self.window_days = settings.DEAL_HISTORY_WINDOW_DAYS

    def evaluate(self, observation_count: int) -> HistorySufficiency:
        if observation_count == 0:
            status = "NEW_PRODUCT"
            sufficient = False
        elif observation_count < self.min_observations:
            status = "INSUFFICIENT_HISTORY"
            sufficient = False
        elif observation_count < self.high_confidence_observations:
            status = "BASIC_HISTORY"
            sufficient = True
        else:
            status = "HIGH_CONFIDENCE_HISTORY"
            sufficient = True
            
        return HistorySufficiency(
            status=status,
            observation_count=observation_count,
            is_sufficient=sufficient
        )
