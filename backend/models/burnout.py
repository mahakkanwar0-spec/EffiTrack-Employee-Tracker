from pydantic import BaseModel
from typing import Dict


class CompanyBurnoutComparison(BaseModel):
    risk_distribution: Dict[str, float]   # e.g. {"Low": 62.5, "Medium": 25.0, "High": 12.5}
    avg_risk_score: float                 # employee-average risk score (0-100)
    your_risk_score: float                # this employee's risk score (0-100)
    total_employees: int


class BurnoutOut(BaseModel):
    uid: str
    risk_level: str
    risk_label: str
    probabilities: Dict[str, float]
    input_features: Dict[str, float]
    company_comparison: CompanyBurnoutComparison