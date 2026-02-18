from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    app_name: str = "AI PDF Translator"
    environment: str = Field(default="local", description="Environment name")

    # OpenAI / Agents
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for OpenAI-compatible APIs",
    )
    translation_model: str = Field(
        default="gpt-4o-mini",
        description="Model used for translation",
    )

    # File handling
    max_upload_mb: int = Field(default=20, description="Maximum upload size in megabytes")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )


settings = Settings()
