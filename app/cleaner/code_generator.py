from typing import List
from app.models.schemas import CleaningOperation


class CodeGenerator:
    @classmethod
    def generate_pandas_pipeline(cls, operations: List[CleaningOperation], dataset_name: str = "dataset.csv") -> str:
        lines = [
            "# ====================================================================",
            "# DataCleanse AI: Automated Data Cleaning & Transformation Pipeline",
            "# ====================================================================",
            "import pandas as pd",
            "import numpy as np",
            "import re",
            "",
            f"# 1. Load raw dataset",
            f"df = pd.read_csv('{dataset_name}')",
            f"print(f'Initial shape: {{df.shape}}')",
            ""
        ]

        step = 2
        for op in operations:
            if op.operation_type == "DROP_DUPLICATES":
                lines.append(f"# Step {step}: Deduplicate exact duplicate rows")
                lines.append("df.drop_duplicates(inplace=True)")
                lines.append("")
                step += 1

            elif op.operation_type == "IMPUTE_MEDIAN":
                col = op.target_column
                med = op.parameters.get("median", 0.0)
                lines.append(f"# Step {step}: Impute missing numeric values in '{col}' with median")
                lines.append(f"median_val = df['{col}'].median()")
                lines.append(f"df['{col}'].fillna(median_val, inplace=True)")
                lines.append("")
                step += 1

            elif op.operation_type == "CLAMP_OUTLIERS":
                col = op.target_column
                low = op.parameters.get("lower_bound", 0.0)
                high = op.parameters.get("upper_bound", 100.0)
                lines.append(f"# Step {step}: Clamp extreme statistical outliers in '{col}' using IQR bounds")
                lines.append(f"df['{col}'] = df['{col}'].clip(lower={low}, upper={high})")
                lines.append("")
                step += 1

            elif op.operation_type == "STANDARDIZE_DATES":
                col = op.target_column
                lines.append(f"# Step {step}: Standardize dates in '{col}' to ISO 8601 (YYYY-MM-DD)")
                lines.append(f"df['{col}'] = pd.to_datetime(df['{col}'], errors='coerce').dt.strftime('%Y-%m-%d')")
                lines.append("")
                step += 1

            elif op.operation_type == "MASK_PII":
                col = op.target_column
                lines.append(f"# Step {step}: Mask sensitive Social Security Numbers in '{col}'")
                lines.append(f"df['{col}'] = df['{col}'].astype(str).str.replace(r'\\b\\d{{3}}-\\d{{2}}-(\\d{{4}})\\b', r'***-**-\\1', regex=True)")
                lines.append("")
                step += 1

        lines.extend([
            f"# Final validation",
            f"print(f'Cleaned shape: {{df.shape}}')",
            f"df.to_csv('cleaned_{dataset_name}', index=False)",
            f"print('Successfully exported cleaned_{dataset_name}')"
        ])

        return "\n".join(lines)

