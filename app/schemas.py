from pydantic import BaseModel
from datetime import date
from typing import Optional, List, Dict, Any

class SalesRequest(BaseModel):
    sku: str
    date: date
    quantity: float

class ProductionRequest(BaseModel):
    sku: str
    date: date
    quantity: float

class InventoryRequest(BaseModel):
    sku: str
    date: date
    quantity: float

class ForecastResponse(BaseModel):
    sku: str
    forecast_data: List[Dict[str, Any]]
    chart_data: Dict[str, Any]
    days_ahead: int
    
class RecommendationResponse(BaseModel):
    sku: str
    recommended_quantity: float
    current_stock: Optional[float] = None
    forecasted_demand: Optional[float] = None
    safety_stock: Optional[float] = None
    reasoning: str

class StatusResponse(BaseModel):
    status: str
    message: str
    timestamp: str