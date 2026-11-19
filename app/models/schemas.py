from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ColumnProfile(BaseModel):
    name: str
    inferred_type: str  # numeric, categorical, datetime, text
    total_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    sample_values: List[Any]
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None


class AnomalyFinding(BaseModel):
    id: str
    column: str
    anomaly_type: str  # MISSING_VALUES, OUTLIERS, PII_LEAK, DATE_FORMAT_DRIFT, DUPLICATES
    severity: str      # HIGH, MEDIUM, LOW
    affected_rows_count: int
    description: str
    suggested_fix: str


class DatasetProfile(BaseModel):
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    data_health_score: float  # 0 to 100
    anomalies: List[AnomalyFinding]
    duplicate_rows_count: int


class CleaningOperation(BaseModel):
    operation_type: str  # IMPUTE_MEDIAN, IMPUTE_MODE, CLAMP_OUTLIERS, STANDARDIZE_DATES, STRIP_WHITESPACE, MASK_PII, DROP_DUPLICATES
    target_column: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    rationale: str


class CleaningResult(BaseModel):
    initial_health_score: float
    cleaned_health_score: float
    operations_applied: List[CleaningOperation]
    before_rows_sample: List[Dict[str, Any]]
    after_rows_sample: List[Dict[str, Any]]
    rows_affected: int
    generated_python_code: str
    cleaned_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class IngestDataRequest(BaseModel):
    csv_or_json: str = Field(..., min_length=20, description="Raw CSV string or JSON array of records")
    dataset_name: Optional[str] = "dataset.csv"

