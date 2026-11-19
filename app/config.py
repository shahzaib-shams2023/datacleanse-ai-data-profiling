from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "DataCleanse AI Tabular Profiling & Cleaning Copilot"
    host: str = "0.0.0.0"
    port: int = 8007
    environment: str = "development"

    max_sample_rows: int = 1000
    iqr_outlier_factor: float = 1.5

    llm_api_key: Optional[str] = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

