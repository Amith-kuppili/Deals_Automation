from pydantic import BaseModel
from typing import Optional

class HistorySufficiency(BaseModel):
    status: str # 'NEW_PRODUCT', 'INSUFFICIENT_HISTORY', 'BASIC_HISTORY', 'HIGH_CONFIDENCE_HISTORY'
    observation_count: int
    is_sufficient: bool
