from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List
from pathlib import Path

class Settings(BaseSettings):
    """Pydantic configuration settings for the AccessLens application."""

    # API Settings
    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")
    debug: bool = Field(False, alias="DEBUG")

    # Browser Settings
    browser_headless: bool = Field(True, alias="BROWSER_HEADLESS")
    browser_max_pages: int = Field(5, alias="BROWSER_MAX_PAGES")
    browser_timeout: int = Field(30000, alias="BROWSER_TIMEOUT")

    # Audit Settings
    default_viewport_width: int = Field(1280, alias="VIEWPORT_WIDTH")
    default_viewport_height: int = Field(720, alias="VIEWPORT_HEIGHT")
    max_audit_duration: int = Field(300, alias="MAX_AUDIT_DURATION")

    # Engine Settings
    enabled_engines: List[str] = Field(
        ["wcag_deterministic", "contrast_engine", "structural_engine", "ai_engine"],
        alias="ENABLED_ENGINES"
    )

    # Thresholds
    contrast_thresholds: dict = Field(
        default_factory=lambda: {
            "body_text": 4.5,
            "large_text": 3.0,
            "ui_component": 3.0,
            "graphical_object": 3.0
        },
        alias="CONTRAST_THRESHOLDS"
    )

    # Confidence Weights
    confidence_weights: dict = Field(
        default_factory=lambda: {
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
        alias="CONFIDENCE_WEIGHTS"
    )

    # AI Model Settings
    llava_model_path: Path = Field(Path("./models/llava"), alias="LLAVA_MODEL_PATH")
    mistral_model_path: Path = Field(Path("./models/mistral-7b"), alias="MISTRAL_MODEL_PATH")
    ai_use_local: bool = Field(True, alias="AI_USE_LOCAL")
    ai_confidence_threshold: float = Field(0.7, alias="AI_CONFIDENCE_THRESHOLD")

    # AI Endpoints
    llava_endpoint: str = Field("http://localhost:8001", alias="LLAVA_ENDPOINT")
    mistral_endpoint: str = Field("http://localhost:8002", alias="MISTRAL_ENDPOINT")

    # Infrastructure
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")
    redis_url: Optional[str] = Field(None, alias="REDIS_URL")

    # Storage
    storage_path: Path = Field(Path("./data"), alias="STORAGE_PATH")

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: Optional[Path] = Field(None, alias="LOG_FILE")
    json_logs: bool = Field(True, alias="JSON_LOGS")

    # Security
    cors_origins: str = Field("http://localhost:3000", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()


settings.llava_model_path.parent.mkdir(parents=True, exist_ok=True)
settings.mistral_model_path.parent.mkdir(parents=True, exist_ok=True)
settings.storage_path.mkdir(parents=True, exist_ok=True)