import pytest
from app.profiler.statistical import TabularProfiler
from app.cleaner.transformer import DataTransformer
from app.cleaner.code_generator import CodeGenerator
from app.data.sample_dirty_data import SAMPLE_DIRTY_CSV


def test_transformer_cleans_dirty_data():
    rows = TabularProfiler.parse_data(SAMPLE_DIRTY_CSV)
    profile, cols = TabularProfiler.profile_dataset(rows)
    cleaned, ops = DataTransformer.apply_cleaning(rows, cols, profile.data_health_score)

    # Duplicates removed: 11 -> 10
    assert len(cleaned) == 10

    # Nulls in monthly_revenue imputed
    assert all(r.get("monthly_revenue") is not None for r in cleaned)

    # Extreme outlier (999999.0) clamped
    assert all(r["monthly_revenue"] < 100000.0 for r in cleaned)

    # Dates standardized to YYYY-MM-DD
    for r in cleaned:
        assert "-" in r["signup_date"]
        assert "/" not in r["signup_date"]

    # PII masked
    for r in cleaned:
        assert "***-**-" in r["ssn_identification"]


def test_code_generator_produces_pandas_script():
    rows = TabularProfiler.parse_data(SAMPLE_DIRTY_CSV)
    profile, cols = TabularProfiler.profile_dataset(rows)
    cleaned, ops = DataTransformer.apply_cleaning(rows, cols, profile.data_health_score)
    script = CodeGenerator.generate_pandas_pipeline(ops, "test.csv")

    assert "import pandas as pd" in script
    assert "df.drop_duplicates" in script
    assert "df['monthly_revenue'].fillna" in script

