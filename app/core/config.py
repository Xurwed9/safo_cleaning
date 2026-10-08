from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Safo Cleaning API"
    debug: bool = False

    database_url: str
    secret_key: str

    telegram_bot_token: str
    telegram_chat_id: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()