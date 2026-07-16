from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./demandweave.db"
    jwt_secret: str = "local-jwt-secret"
    mandate_secret: str = "local-mandate-secret"
    access_token_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
