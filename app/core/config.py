from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Unirides"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()