from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "My Backend"
    debug: bool = False
    cors_origins: list[str] = ["https://aclarity.netlify.app/"]
    firebase_credentials_path: str = "serviceAccountKey.json"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
