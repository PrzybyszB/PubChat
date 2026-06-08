from pydantic import BaseModel

class ReportRequest(BaseModel):
    nutrient: str
    min_value: float
    max_value: float

class StatisticsResult(BaseModel):
    mean_value: float
    median_value: float
    p90_value: float

    pct_low: float
    pct_normal: float
    pct_high: float

    problem: str