import re
from typing import List, Dict, Any
from app.models.schemas import AnomalyFinding, ColumnProfile, DatasetProfile


class AnomalyDetector:
    PII_PATTERNS = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "Unmasked Social Security Number (SSN) detected"),
        (r"\b(?:\d{4}[ -]?){3}\d{4}\b", "Unmasked Credit Card Number detected")
    ]

    DATE_PATTERNS = [
        (r"^\d{4}-\d{2}-\d{2}$", "ISO_8601"),
        (r"^\d{1,2}/\d{1,2}/\d{4}$", "US_STANDARD"),
        (r"^\d{1,2}-\d{1,2}-\d{4}$", "HYPHEN_STANDARD")
    ]

    @classmethod
    def detect_anomalies(cls, rows: List[Dict[str, Any]], columns: List[ColumnProfile]) -> List[AnomalyFinding]:
        findings: List[AnomalyFinding] = []

        # 1. Check Missing Values per Column
        for col in columns:
            if col.missing_percentage > 5.0:
                findings.append(AnomalyFinding(
                    id=f"ANOM-MISSING-{col.name}",
                    column=col.name,
                    anomaly_type="MISSING_VALUES",
                    severity="HIGH" if col.missing_percentage > 20.0 else "MEDIUM",
                    affected_rows_count=col.missing_count,
                    description=f"Column '{col.name}' exhibits a high missing rate of {col.missing_percentage}% ({col.missing_count} rows).",
                    suggested_fix=f"Impute missing values with column {'median' if col.inferred_type == 'numeric' else 'mode'} or drop empty rows."
                ))

        # 2. Check Numeric Outliers using IQR
        for col in columns:
            if col.inferred_type == "numeric":
                num_vals = [float(r[col.name]) for r in rows if r.get(col.name) is not None and isinstance(r[col.name], (int, float))]
                if len(num_vals) >= 6:
                    sorted_vals = sorted(num_vals)
                    q1 = sorted_vals[len(sorted_vals) // 4]
                    q3 = sorted_vals[(3 * len(sorted_vals)) // 4]
                    iqr = q3 - q1
                    lower_bound = q1 - (1.5 * iqr)
                    upper_bound = q3 + (1.5 * iqr)

                    outliers = [v for v in num_vals if v < lower_bound or v > upper_bound]
                    if outliers:
                        findings.append(AnomalyFinding(
                            id=f"ANOM-OUTLIER-{col.name}",
                            column=col.name,
                            anomaly_type="OUTLIERS",
                            severity="MEDIUM",
                            affected_rows_count=len(outliers),
                            description=(
                                f"Statistical IQR evaluation identified {len(outliers)} extreme outliers in '{col.name}' "
                                f"(bounds: [{lower_bound:.1f}, {upper_bound:.1f}], observed values: {outliers[:2]})."
                            ),
                            suggested_fix=f"Winsorize or clamp extreme values to IQR bounds [{lower_bound:.1f}, {upper_bound:.1f}]."
                        ))

        # 3. Check PII Leaks
        for col in columns:
            str_vals = [str(r.get(col.name)) for r in rows if r.get(col.name) is not None]
            for pattern, desc in cls.PII_PATTERNS:
                leak_count = sum(1 for v in str_vals if re.search(pattern, v))
                if leak_count > 0:
                    findings.append(AnomalyFinding(
                        id=f"ANOM-PII-{col.name}",
                        column=col.name,
                        anomaly_type="PII_LEAK",
                        severity="HIGH",
                        affected_rows_count=leak_count,
                        description=f"Sensitive PII alert: {desc} in column '{col.name}' across {leak_count} entries.",
                        suggested_fix="Anonymize or hash PII values (e.g., mask with '***-**-XXXX')."
                    ))

        # 4. Check Date Format Drift
        for col in columns:
            str_vals = [str(r.get(col.name)) for r in rows if r.get(col.name) is not None]
            format_counts = {}
            for v in str_vals:
                for pattern, fmt_name in cls.DATE_PATTERNS:
                    if re.match(pattern, v):
                        format_counts[fmt_name] = format_counts.get(fmt_name, 0) + 1

            if len(format_counts) > 1:
                findings.append(AnomalyFinding(
                    id=f"ANOM-DATE-DRIFT-{col.name}",
                    column=col.name,
                    anomaly_type="DATE_FORMAT_DRIFT",
                    severity="MEDIUM",
                    affected_rows_count=len(str_vals),
                    description=f"Inconsistent date representations detected in '{col.name}': {dict(format_counts)}.",
                    suggested_fix="Standardize all date entries to ISO 8601 (YYYY-MM-DD)."
                ))

        return findings

