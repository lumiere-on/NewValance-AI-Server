from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

ROOT_DIR = Path(__file__).resolve().parents[2]   # app/../../

class Settings(BaseSettings):
    # === OpenAI ===
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    # === Google TTS ===
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(..., env="GOOGLE_APPLICATION_CREDENTIALS")
    # === AWS S3 ===
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field("ap-northeast-2", env="AWS_REGION")
    S3_BUCKET: str = Field("news-shortform", env="S3_BUCKET")
    BE_SERVER_URL: str = Field("BE-SERVER-URL", env="BE_SERVER_URL")

    class Config:
        env_file = ROOT_DIR / ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()
