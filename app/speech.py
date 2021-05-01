import base64
import io
from threading import Lock

from fastapi import APIRouter, Response
from minio import Minio

from app.settings import Settings
from app.utils import object_exists, obtain_audio


def create_speech_router(audio_lock: Lock, counter_lock: Lock, settings: Settings) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def read_root() -> dict:
        message = (
            f"Hello world! From FastAPI running on Uvicorn with Gunicorn. Using Python"
        )
        return {"message": message}

    @router.get("/speech/")
    async def speech(text: str = "Example") -> Response:
        real_key_suffix_bytes = base64.b64encode(text.encode("utf-8"))
        real_key_suffix = str(real_key_suffix_bytes, "utf-8")
        real_key = f"{settings.audio_folder}/{real_key_suffix}"

        client: Minio = Minio(
            Settings().minio_url,
            access_key=Settings().minio_access_key,
            secret_key=Settings().minio_secret_key,
            secure=False,
        )

        # Make bucket if missing.
        found = client.bucket_exists(f"{settings.bucket_name}")
        if not found:
            client.make_bucket(settings.bucket_name)
        else:
            print(f"Bucket '{settings.bucket_name}' already exists")

        with audio_lock:
            audio_object_exists = object_exists(client, settings.bucket_name, real_key)
            if not audio_object_exists:
                content = obtain_audio(text)

                client.put_object(settings.bucket_name, real_key, io.BytesIO(content), len(content))
                print(f"'Successfully uploaded object '{text}' to bucket '{settings.bucket_name}'.")

        counter = 0
        with counter_lock:
            counter_object_exists = object_exists(client, settings.bucket_name, settings.counter_name)
            if counter_object_exists:
                try:
                    counter_response = client.get_object(settings.bucket_name, settings.counter_name)
                    counter = int(counter_response.data)
                finally:
                    counter_response.close()
                    counter_response.release_conn()

            if not audio_object_exists:
                new_counter = counter + len(text)
                if new_counter > Settings().gcp_counter_limit:
                    # TODO handle limit reached
                    return Response(status_code=503)

                counter = new_counter
                counter_str = str(counter)
                counter_bytes = bytes(counter_str, "utf-8")
                counter_stream = io.BytesIO(counter_bytes)
                client.put_object(settings.bucket_name, settings.counter_name, counter_stream, len(counter_bytes))

        try:
            key_response = client.get_object(settings.bucket_name, real_key)
            stored_content = key_response.data
        finally:
            key_response.close()
            key_response.release_conn()

        return Response(stored_content, status_code=200, media_type="audio/mp3")

    return router
