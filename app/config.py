from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    OPENAI_API_KEY: str
    WEBHOOK_URL: str = ""
    SECRET_TOKEN: str = "autopilot_secret"
    PORT: int = 8080
    SUPERADMIN_ID: int = 1207611858
    KASPI_PHONE: str = "+77077727528"
    SUBSCRIPTION_PRICE: int = 5000
    TRIAL_HOURS: int = 12

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
