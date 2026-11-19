# DataCleanse AI: Tabular Profiling & Automated Cleaning Copilot

DataCleanse AI is an automated data engineering copilot designed to profile tabular datasets (CSV / JSON), calculate comprehensive statistical health scores, detect anomalous contamination (IQR statistical outliers, unmasked PII, date format drift, duplicate records), execute automated cleaning transformations, and synthesize production-ready Python/Pandas scripts.

---

## 🔍 The Problem
Data scientists and analytics engineers spend an estimated 80% of their project time manually inspecting and cleaning dirty data:
- **Silent Schema & Format Drift**: Inconsistent date conventions (`YYYY-MM-DD` vs `MM/DD/YYYY`) and whitespace noise break downstream pipelines.
- **Extreme Statistical Outliers**: Erroneous values (e.g. integer overflows, typo numbers) skew gradient descent models and financial aggregation metrics.
- **PII Contamination Risks**: Unmasked Social Security Numbers, credit cards, or phone numbers leak into training corpora, violating GDPR and HIPAA compliance.

## 💡 The Solution
DataCleanse AI provides an end-to-end automated data audit and cleaning workflow:
1. **Statistical Profiler**: Computes column types, null percentages, distinct cardinalities, min/max/mean/median, and calculates a baseline Data Health Score (0-100).
2. **Multi-Vector Anomaly Detection**:
   - Outliers: Interquartile Range (IQR) boundary evaluation (`1.5 * IQR`).
   - PII Leakage: Regular expression scanners for SSNs, credit cards, and emails.
   - Date Drift: Regex pattern recognition across international date conventions.
   - Duplicate Rows: In-memory hash deduplication.
3. **Automated Cleaning Operations**:
   - Imputes missing values with column median (numeric) or mode (categorical).
   - Clamps extreme statistical outliers to IQR bounds.
   - Standardizes date formats to ISO 8601 (`YYYY-MM-DD`).
   - Redacts PII with privacy-preserving masks (`***-**-XXXX`).
4. **Executable Pandas Script Synthesis**: Generates clean, reproducible, commented Python code ready for Airflow or Prefect production pipelines.

---

## 🏛️ System Architecture

```
Raw Tabular Dataset (CSV / JSON)
                 │
                 ▼
     [Statistical Profiler]
      - Null %, unique counts
      - Min / Max / Mean / Median
      - Baseline Data Health Score
                 │
                 ▼
     [Anomaly & PII Detector]
      - IQR outlier calculation
      - PII regex scanner (SSN, CC)
      - Date format drift detection
      - Exact row deduplication
                 │
                 ▼
     [Transformation Engine]
      - Median / mode imputation
      - Outlier clipping
      - ISO date standardization
      - PII cryptographic masking
                 │
                 ▼
  [Pandas Python Code Generator]
                 │
                 ▼
Interactive Studio, Tabular Diff & REST API
```

---

## 🛠️ Technology Stack
- **Backend**: Python 3.11, FastAPI, Pydantic v2
- **Data Engine**: Tabular Statistics Engine (IQR Outlier & Regex PII Scanners)
- **Frontend**: Data Engineering Workbench (Tailwind CSS, FontAwesome)
- **Testing**: Pytest, Starlette TestClient
- **Deployment**: Docker, Docker Compose, GitHub Actions CI

---

## 🚀 Getting Started

### Installation
```bash
cd datacleanse-ai-data-profiling

# Create virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Running the Application
```bash
python -m uvicorn app.main:app --reload --port 8007
```
Access the DataCleanse Studio at `http://localhost:8007` or inspect OpenAPI docs at `http://localhost:8007/docs`.

---

## 🧪 Running Automated Tests
```bash
pytest tests/ -v
```

---

## 🐳 Docker Deployment
```bash
docker compose up --build
```
Access the application at `http://localhost:8007`.

---

## 📡 API Reference

### Profile Dataset
`POST /api/profile`
```json
{
  "csv_or_json": "id,customer_name,monthly_revenue\n101,Acme,1200.0\n102,Globex,999999.0"
}
```

Response:
```json
{
  "row_count": 2,
  "column_count": 3,
  "data_health_score": 68.5,
  "anomalies": [
    {
      "column": "monthly_revenue",
      "anomaly_type": "OUTLIERS",
      "severity": "MEDIUM",
      "description": "Statistical IQR evaluation identified extreme outliers...",
      "suggested_fix": "Winsorize or clamp extreme values..."
    }
  ]
}
```

### Clean Dataset & Generate Script
`POST /api/clean`
```json
{
  "csv_or_json": "id,customer_name,monthly_revenue\n101,Acme,1200.0\n102,Globex,999999.0"
}
```

Response:
```json
{
  "initial_health_score": 68.5,
  "cleaned_health_score": 96.0,
  "operations_applied": [
    {
      "operation_type": "CLAMP_OUTLIERS",
      "target_column": "monthly_revenue",
      "rationale": "Clamped extreme outliers..."
    }
  ],
  "generated_python_code": "import pandas as pd\n..."
}
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

