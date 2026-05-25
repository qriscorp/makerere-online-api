from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/makerere_online"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    frontend_url: str = "http://localhost:8080"
    cors_origins: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
