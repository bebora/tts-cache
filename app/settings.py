from pydantic import BaseSettings


class Settings(BaseSettings):
    audio_folder: str = "audio"
    bucket_name: str = "speech"
    counter_name: str = "counter"
    minio_url: str
    minio_access_key: str
    minio_secret_key: str
    gcp_counter_limit: int
    gcp_language: str
    gcp_voice_name: str
    google_application_credentials: str
    audio_expiry: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        secrets_dir = "/run/secrets"
