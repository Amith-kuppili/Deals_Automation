from pydantic import BaseModel
from typing import List, Optional

class ReefAPIPriceObservation(BaseModel):
    price: float
    observed_at: str
    availability: bool = True
    seller: Optional[str] = None

class ReefAPIHistoryResponse(BaseModel):
    product_id: str
    platform: str
    history: List[ReefAPIPriceObservation]
