from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "prod"
    API_BASE_URL: str = "http://127.0.0.1:8000"
    DATABASE_URL: str
    SECRET_KEY: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Unirides"
    GOOGLE_MAPS_API_KEY: str
    TEST_DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()