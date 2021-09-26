import json
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseSettings


class LanguageSetting(BaseSettings):
    gcp_language: str
    gcp_voice_name: str


def json_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A simple settings source that loads variables from a JSON file
    at the project's root.
    """
    encoding = settings.__config__.env_file_encoding
    return json.loads(Path("config.json").read_text(encoding))


class Settings(BaseSettings):
    audio_folder: str = "audio"
    bucket_name: str = "speech"
    counter_name: str = "counter"
    minio_url: str
    minio_access_key: str
    minio_secret_key: str
    gcp_counter_limit: int
    languages: Dict[str, LanguageSetting]
    google_application_credentials: str
    audio_expiry: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        secrets_dir = "/run/secrets"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                json_config_settings_source,
                env_settings,
                file_secret_settings,
            )
