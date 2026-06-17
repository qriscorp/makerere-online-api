from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/makerere_online"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    frontend_url: str = "http://localhost:8080"
    cors_origins: str = ""
    password_reset_expire_minutes: int = 60
    email_verification_expire_minutes: int = 15
    email_verification_max_attempts: int = 5
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
