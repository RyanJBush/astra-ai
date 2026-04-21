from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Astra AI"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://astra:astra@postgres:5432/astra"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    daily_research_quota: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ASTRA_")


settings = Settings()
