import csv
import json
import io
import math
from typing import List, Dict, Any, Tuple
from app.models.schemas import ColumnProfile, DatasetProfile, AnomalyFinding


class TabularProfiler:
    @classmethod
    def parse_data(cls, raw_input: str) -> List[Dict[str, Any]]:
        raw = raw_input.strip()
        # Try JSON
        if raw.startswith("[") and raw.endswith("]"):
            try:
                data = json.loads(raw)
                if isinstance(data, list) and all(isinstance(r, dict) for r in data):
                    return data
            except Exception:
                pass

        # Try CSV
        reader = csv.DictReader(io.StringIO(raw))
        rows = []
        for r in reader:
            cleaned_row = {}
            for k, v in r.items():
                if k is None:
                    continue
                val = v.strip() if isinstance(v, str) else v
                if val == "" or val.lower() in ("null", "none", "nan", "n/a"):
                    cleaned_row[k.strip()] = None
                else:
                    # Try numeric conversion
                    try:
                        if "." in val:
                            cleaned_row[k.strip()] = float(val)
                        else:
                            cleaned_row[k.strip()] = int(val)
                    except ValueError:
                        cleaned_row[k.strip()] = val
            rows.append(cleaned_row)
        return rows

    @classmethod
    def profile_dataset(cls, rows: List[Dict[str, Any]]) -> Tuple[DatasetProfile, List[ColumnProfile]]:
        if not rows:
            return DatasetProfile(
                row_count=0,
                column_count=0,
                columns=[],
                data_health_score=0.0,
                anomalies=[],
                duplicate_rows_count=0
            ), []

        columns = list(rows[0].keys())
        col_profiles: List[ColumnProfile] = []

        total_cells = len(rows) * len(columns)
        total_missing = 0

        for col in columns:
            vals = [r.get(col) for r in rows]
            missing_cnt = sum(1 for v in vals if v is None)
            total_missing += missing_cnt
            valid_vals = [v for v in vals if v is not None]
            unique_cnt = len(set(str(v) for v in valid_vals))

            # Infer type
            num_vals = []
            for v in valid_vals:
                if isinstance(v, (int, float)):
                    num_vals.append(float(v))

            is_numeric = len(num_vals) > (len(valid_vals) * 0.7) if valid_vals else False

            min_v, max_v, mean_v, median_v = None, None, None, None
            if is_numeric and num_vals:
                inferred_type = "numeric"
                min_v = round(min(num_vals), 2)
                max_v = round(max(num_vals), 2)
                mean_v = round(sum(num_vals) / len(num_vals), 2)
                sorted_nums = sorted(num_vals)
                mid = len(sorted_nums) // 2
                median_v = round(
                    sorted_nums[mid] if len(sorted_nums) % 2 != 0 else (sorted_nums[mid - 1] + sorted_nums[mid]) / 2,
                    2
                )
            else:
                inferred_type = "categorical"

            col_profiles.append(ColumnProfile(
                name=col,
                inferred_type=inferred_type,
                total_count=len(rows),
                missing_count=missing_cnt,
                missing_percentage=round((missing_cnt / len(rows)) * 100, 2),
                unique_count=unique_cnt,
                sample_values=[v for v in valid_vals[:3]],
                min_value=min_v,
                max_value=max_v,
                mean_value=mean_v,
                median_value=median_v
            ))

        # Check duplicates
        seen_rows = set()
        dup_count = 0
        for r in rows:
            row_tuple = tuple(sorted((k, str(v)) for k, v in r.items()))
            if row_tuple in seen_rows:
                dup_count += 1
            else:
                seen_rows.add(row_tuple)

        # Baseline Data Health Score calculation
        base_score = 100.0
        missing_rate = (total_missing / max(total_cells, 1)) * 100
        base_score -= (missing_rate * 1.5)
        base_score -= (dup_count * 5.0)

        health_score = round(max(min(base_score, 100.0), 10.0), 1)

        profile = DatasetProfile(
            row_count=len(rows),
            column_count=len(columns),
            columns=col_profiles,
            data_health_score=health_score,
            anomalies=[],
            duplicate_rows_count=dup_count
        )
        return profile, col_profiles

