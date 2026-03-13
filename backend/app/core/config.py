
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from pathlib import Path

class Settings(BaseSettings):

    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    debug: bool = Field(False, env="DEBUG")


    browser_headless: bool = Field(True, env="BROWSER_HEADLESS")
    browser_max_pages: int = Field(5, env="BROWSER_MAX_PAGES")
    browser_timeout: int = Field(30000, env="BROWSER_TIMEOUT")


    default_viewport_width: int = Field(1280, env="VIEWPORT_WIDTH")
    default_viewport_height: int = Field(720, env="VIEWPORT_HEIGHT")
    max_audit_duration: int = Field(300, env="MAX_AUDIT_DURATION")


    enabled_engines: List[str] = Field(
        ["wcag_deterministic", "contrast_engine", "structural_engine", "ai_engine"],
        env="ENABLED_ENGINES"
    )


    contrast_thresholds: dict = Field(
        {
            "body_text": 4.5,
            "large_text": 3.0,
            "ui_component": 3.0,
            "graphical_object": 3.0
        },
        env="CONTRAST_THRESHOLDS"
    )


    confidence_weights: dict = Field(
        {
            "contrast": {
                "detection_reliability": 0.98,
                "context_clarity": 0.95,
                "pattern_match": 0.9,
                "evidence_quality": 1.0
            },
            "structural": {
                "detection_reliability": 0.9,
                "context_clarity": 0.85,
                "pattern_match": 0.9,
                "evidence_quality": 0.85
            },
            "navigation": {
                "detection_reliability": 0.95,
                "context_clarity": 0.9,
                "pattern_match": 0.95,
                "evidence_quality": 0.9
            }
        },
        env="CONFIDENCE_WEIGHTS"
    )


    llava_model_path: Path = Field(..., env="LLAVA_MODEL_PATH")
    mistral_model_path: Path = Field(..., env="MISTRAL_MODEL_PATH")
    ai_use_local: bool = Field(True, env="AI_USE_LOCAL")
    ai_confidence_threshold: float = Field(0.7, env="AI_CONFIDENCE_THRESHOLD")


    llava_endpoint: str = Field("http://localhost:8001", env="LLAVA_ENDPOINT")
    mistral_endpoint: str = Field("http://localhost:8002", env="MISTRAL_ENDPOINT")


    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(None, env="REDIS_URL")


    storage_path: Path = Field(Path("./data"), env="STORAGE_PATH")


    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[Path] = Field(None, env="LOG_FILE")
    json_logs: bool = Field(True, env="JSON_LOGS")


    cors_origins: str = Field("http://localhost:3000", env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()


settings.llava_model_path.parent.mkdir(parents=True, exist_ok=True)
settings.mistral_model_path.parent.mkdir(parents=True, exist_ok=True)
settings.storage_path.mkdir(parents=True, exist_ok=True)