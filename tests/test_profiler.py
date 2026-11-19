import pytest
from app.profiler.statistical import TabularProfiler
from app.data.sample_dirty_data import SAMPLE_DIRTY_CSV


def test_parse_csv_data():
    rows = TabularProfiler.parse_data(SAMPLE_DIRTY_CSV)
    assert len(rows) == 11
    assert "customer_name" in rows[0]
    assert "monthly_revenue" in rows[0]


def test_profile_dataset_statistics():
    rows = TabularProfiler.parse_data(SAMPLE_DIRTY_CSV)
    profile, cols = TabularProfiler.profile_dataset(rows)
    assert profile.row_count == 11
    assert profile.column_count == 6
    assert profile.duplicate_rows_count == 1
    assert 0.0 <= profile.data_health_score <= 100.0

    rev_col = next(c for c in cols if c.name == "monthly_revenue")
    assert rev_col.inferred_type == "numeric"
    assert rev_col.missing_count >= 1
    assert rev_col.median_value is not None

