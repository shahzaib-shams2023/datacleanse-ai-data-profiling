import re
import copy
from typing import List, Dict, Any, Tuple
from app.models.schemas import CleaningOperation, ColumnProfile, CleaningResult


class DataTransformer:
    @classmethod
    def apply_cleaning(
        cls,
        rows: List[Dict[str, Any]],
        columns: List[ColumnProfile],
        initial_score: float
    ) -> Tuple[List[Dict[str, Any]], List[CleaningOperation]]:
        cleaned_rows = copy.deepcopy(rows)
        operations: List[CleaningOperation] = []

        # 1. Deduplicate rows
        seen = set()
        deduped = []
        dup_count = 0
        for r in cleaned_rows:
            key = tuple(sorted((k, str(v)) for k, v in r.items()))
            if key in seen:
                dup_count += 1
            else:
                seen.add(key)
                deduped.append(r)

        if dup_count > 0:
            operations.append(CleaningOperation(
                operation_type="DROP_DUPLICATES",
                target_column="*",
                rationale=f"Removed {dup_count} exact duplicate rows."
            ))
            cleaned_rows = deduped

        # 2. Impute Missing Values & Outliers
        for col in columns:
            name = col.name
            if col.inferred_type == "numeric":
                vals = [r[name] for r in cleaned_rows if r.get(name) is not None and isinstance(r[name], (int, float))]
                if vals:
                    # Median imputation
                    sorted_vals = sorted(vals)
                    mid = len(sorted_vals) // 2
                    median_val = sorted_vals[mid]

                    imputed_count = 0
                    for r in cleaned_rows:
                        if r.get(name) is None or not isinstance(r.get(name), (int, float)):
                            r[name] = median_val
                            imputed_count += 1

                    if imputed_count > 0:
                        operations.append(CleaningOperation(
                            operation_type="IMPUTE_MEDIAN",
                            target_column=name,
                            parameters={"median": median_val},
                            rationale=f"Imputed {imputed_count} nulls in '{name}' with median value ({median_val})."
                        ))

                    # IQR outlier clamping
                    if len(sorted_vals) >= 6:
                        q1 = sorted_vals[len(sorted_vals) // 4]
                        q3 = sorted_vals[(3 * len(sorted_vals)) // 4]
                        iqr = q3 - q1
                        low_bound = round(q1 - (1.5 * iqr), 2)
                        up_bound = round(q3 + (1.5 * iqr), 2)

                        clamped_count = 0
                        for r in cleaned_rows:
                            if r[name] < low_bound:
                                r[name] = low_bound
                                clamped_count += 1
                            elif r[name] > up_bound:
                                r[name] = up_bound
                                clamped_count += 1

                        if clamped_count > 0:
                            operations.append(CleaningOperation(
                                operation_type="CLAMP_OUTLIERS",
                                target_column=name,
                                parameters={"lower_bound": low_bound, "upper_bound": up_bound},
                                rationale=f"Clamped {clamped_count} extreme statistical outliers in '{name}' to [{low_bound}, {up_bound}]."
                            ))

            elif col.inferred_type == "categorical":
                # Strip whitespace & standardize strings
                for r in cleaned_rows:
                    if isinstance(r.get(name), str):
                        r[name] = r[name].strip()

                # Check date formatting (e.g. MM/DD/YYYY -> YYYY-MM-DD)
                date_fixed_count = 0
                for r in cleaned_rows:
                    val = str(r.get(name) or "")
                    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", val)
                    if m:
                        month, day, year = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
                        r[name] = f"{year}-{month}-{day}"
                        date_fixed_count += 1

                if date_fixed_count > 0:
                    operations.append(CleaningOperation(
                        operation_type="STANDARDIZE_DATES",
                        target_column=name,
                        rationale=f"Standardized {date_fixed_count} datetime values in '{name}' to ISO 8601 (YYYY-MM-DD)."
                    ))

                # Mask PII (e.g. SSNs)
                pii_masked_count = 0
                for r in cleaned_rows:
                    val = str(r.get(name) or "")
                    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", val):
                        r[name] = re.sub(r"\b\d{3}-\d{2}-(\d{4})\b", r"***-**-\1", val)
                        pii_masked_count += 1

                if pii_masked_count > 0:
                    operations.append(CleaningOperation(
                        operation_type="MASK_PII",
                        target_column=name,
                        rationale=f"Redacted sensitive Social Security Numbers in '{name}' with SHA-safe mask '***-**-XXXX'."
                    ))

        return cleaned_rows, operations

