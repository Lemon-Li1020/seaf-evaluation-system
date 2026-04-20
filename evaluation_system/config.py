"""
Configuration management for Seaf Evaluation System.
All configuration through Pydantic BaseSettings, no os.getenv string concatenation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_prefix="EVAL_",
        extra="ignore",
        case_sensitive=False,
    )
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    
    # Database
    db_url: str = "sqlite+aiosqlite:///./evaluation.db"
    
    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    
    # LLM
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_api_key: str = Field(default="", description="LLM API Key")
    llm_base_url: str = "https://api.deepseek.com"
    llm_timeout: int = 30
    llm_max_retries: int = 3
    llm_temperature: float = 0.1
    
    # Seaf API
    seaf_api_base: str = Field(default="http://localhost:9000", description="Seaf API base URL")
    seaf_api_key: str = Field(default="", description="Seaf API Key")
    
    # Evaluation
    evaluation_reasoning_timeout: int = 120
    evaluation_workflow_timeout: int = 300
    evaluation_max_retries: int = 3
    regression_threshold: float = 10.0


# Global settings instance
settings = Settings()
