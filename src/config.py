from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    apprise_url: str = "http://localhost:8000"
    apprise_key: str = "hookshot"
    database_path: str = "/data/hookshot.db"
    activity_retention: int = 10000

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
