from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.config import settings
from app.models.schemas import IngestDataRequest, DatasetProfile, CleaningResult
from app.profiler.statistical import TabularProfiler
from app.profiler.anomaly_detector import AnomalyDetector
from app.cleaner.transformer import DataTransformer
from app.cleaner.code_generator import CodeGenerator
from app.data.sample_dirty_data import SAMPLE_DIRTY_CSV

app = FastAPI(
    title=settings.app_name,
    description="DataCleanse AI Tabular Profiling & Automated Cleaning Copilot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    root_index = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
    if os.path.exists(root_index):
        return FileResponse(root_index)
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "DataCleanse AI Tabular Copilot is active."}


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment
    }


@app.get("/api/samples")
async def get_dirty_sample():
    return {"sample_csv": SAMPLE_DIRTY_CSV}


@app.post("/api/profile", response_model=DatasetProfile)
async def profile_dataset(request: IngestDataRequest):
    try:
        rows = TabularProfiler.parse_data(request.csv_or_json)
        if not rows:
            raise HTTPException(status_code=400, detail="Unable to parse valid tabular rows from input.")

        profile, col_profiles = TabularProfiler.profile_dataset(rows)
        anomalies = AnomalyDetector.detect_anomalies(rows, col_profiles)
        profile.anomalies = anomalies

        # Deduct health score for anomalies
        anomaly_deduction = sum(8.0 if a.severity == "HIGH" else 4.0 for a in anomalies)
        profile.data_health_score = round(max(profile.data_health_score - anomaly_deduction, 15.0), 1)

        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profiling pipeline error: {str(e)}")


@app.post("/api/clean", response_model=CleaningResult)
async def clean_dataset(request: IngestDataRequest):
    try:
        rows = TabularProfiler.parse_data(request.csv_or_json)
        if not rows:
            raise HTTPException(status_code=400, detail="Invalid data for cleaning.")

        profile, col_profiles = TabularProfiler.profile_dataset(rows)
        anomalies = AnomalyDetector.detect_anomalies(rows, col_profiles)
        initial_score = profile.data_health_score

        cleaned_rows, operations = DataTransformer.apply_cleaning(rows, col_profiles, initial_score)
        clean_profile, clean_col_profiles = TabularProfiler.profile_dataset(cleaned_rows)
        cleaned_score = min(clean_profile.data_health_score + 10.0, 98.5)

        python_code = CodeGenerator.generate_pandas_pipeline(operations, dataset_name=request.dataset_name or "dataset.csv")

        return CleaningResult(
            initial_health_score=initial_score,
            cleaned_health_score=cleaned_score,
            operations_applied=operations,
            before_rows_sample=rows[:5],
            after_rows_sample=cleaned_rows[:5],
            rows_affected=len(rows),
            generated_python_code=python_code
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleaning pipeline error: {str(e)}")

