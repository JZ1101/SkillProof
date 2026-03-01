from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str
    gemini_model: str = "gemini-3.1-pro-preview"
    runware_api_key: str = ""
    upload_dir: str = "uploads"
    cert_dir: str = "certificates"
    database_url: str = "sqlite:///skillproof.db"
    base_url: str = "http://localhost:8000"


settings = Settings()
