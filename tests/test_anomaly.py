import pytest
from app.profiler.statistical import TabularProfiler
from app.profiler.anomaly_detector import AnomalyDetector
from app.data.sample_dirty_data import SAMPLE_DIRTY_CSV


def test_detect_anomalies_and_pii():
    rows = TabularProfiler.parse_data(SAMPLE_DIRTY_CSV)
    profile, cols = TabularProfiler.profile_dataset(rows)
    anomalies = AnomalyDetector.detect_anomalies(rows, cols)

    types = [a.anomaly_type for a in anomalies]
    assert "MISSING_VALUES" in types
    assert "OUTLIERS" in types
    assert "PII_LEAK" in types
    assert "DATE_FORMAT_DRIFT" in types

