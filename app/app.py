from threading import Lock

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import Settings
from app.speech import create_speech_router


def create_app() -> FastAPI:
    app = FastAPI()

    audio_lock = Lock()
    counter_lock = Lock()
    settings = Settings()

    app.include_router(create_speech_router(audio_lock, counter_lock, settings))
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    return app
