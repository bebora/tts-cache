from threading import Lock

from fastapi import FastAPI

from app.speech import create_speech_router
from app.settings import Settings


def create_app() -> FastAPI:
    app = FastAPI()

    audio_lock = Lock()
    counter_lock = Lock()
    settings = Settings()

    app.include_router(create_speech_router(audio_lock, counter_lock, settings))

    return app
