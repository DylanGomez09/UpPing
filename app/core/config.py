from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "UpPing API"
    VERSION: str = "1.0.0"

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/app_db"
    )

    JWT_SECRET: str = "cambiar-este-secret-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 30
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 30

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_WINDOW_SECONDS: int = 60


settings = Settings()
