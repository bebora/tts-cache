import base64
import io
from datetime import datetime
from threading import Lock

from fastapi import APIRouter, Response
from fastapi.logger import logger as fastapi_logger
from minio import Minio
from minio.commonconfig import ENABLED, Filter, Tags
from minio.lifecycleconfig import Expiration, LifecycleConfig, Rule
from pydantic import BaseModel

from app.settings import Settings
from app.utils import (AudioFetchException, get_counter_value,
                       initialize_counter, object_exists, obtain_gcp_audio)


class AudioRequest(BaseModel):
    text: str = "Example"


def create_speech_router(
    audio_lock: Lock, counter_lock: Lock, settings: Settings
) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    def read_root() -> dict:
        message = (
            f"Hello world! From FastAPI running on Uvicorn with Gunicorn. Using Python"
        )
        return {"message": message}

    @router.post("/speech/")
    def speech(audio_request: AudioRequest) -> Response:
        text = audio_request.text
        real_key_suffix_bytes = base64.b64encode(text.encode("utf-8"))
        real_key_suffix = str(real_key_suffix_bytes, "utf-8")
        real_key = f"{settings.audio_folder}/{real_key_suffix}"

        client: Minio = Minio(
            settings.minio_url,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )

        try:
            # Make bucket if missing.
            found = client.bucket_exists(f"{settings.bucket_name}")
            if not found:
                client.make_bucket(settings.bucket_name)
                config = LifecycleConfig(
                    [
                        Rule(
                            ENABLED,
                            rule_filter=Filter(prefix="audio/"),
                            rule_id="speech-expiry",
                            expiration=Expiration(days=settings.audio_expiry),
                        ),
                    ],
                )
                client.set_bucket_lifecycle(settings.bucket_name, config)
            else:
                fastapi_logger.debug(f"Bucket '{settings.bucket_name}' already exists")

            counter = 0
            now = datetime.now()
            working_month = f"{now.year}/{now.month}"
            with counter_lock:
                counter_object_exists = object_exists(
                    client, settings.bucket_name, settings.counter_name
                )
                if counter_object_exists:
                    counter = get_counter_value(
                        client,
                        settings.bucket_name,
                        settings.counter_name,
                        working_month,
                    )
                else:
                    initialize_counter(client, settings.bucket_name, settings.counter_name, working_month)
                audio_object_already_exists = object_exists(
                    client, settings.bucket_name, real_key
                )
                if not audio_object_already_exists:
                    new_counter = counter + len(text)
                    if new_counter > settings.gcp_counter_limit:
                        return Response("Limit reached", status_code=500)

                    counter = new_counter
                    counter_str = str(counter)
                    counter_bytes = bytes(counter_str, "utf-8")
                    counter_stream = io.BytesIO(counter_bytes)
                    counter_tags = Tags.new_object_tags()
                    counter_tags["working_month"] = working_month
                    client.put_object(
                        settings.bucket_name,
                        settings.counter_name,
                        counter_stream,
                        len(counter_bytes),
                        tags=counter_tags,
                    )

            # an object may be fetched multiple times,
            # but the counter should never underestimate the Cloud provider usage
            if not audio_object_already_exists:
                try:
                    content = obtain_gcp_audio(
                        text,
                        settings.gcp_language,
                        settings.gcp_voice_name,
                        settings.google_application_credentials,
                    )
                except AudioFetchException as e:
                    fastapi_logger.error(e)
                    return Response(
                        "Unable to obtain audio content from content provider",
                        status_code=500,
                    )
                with audio_lock:
                    client.put_object(
                        settings.bucket_name,
                        real_key,
                        io.BytesIO(content),
                        len(content),
                    )
                    fastapi_logger.debug(
                        f"'Successfully uploaded object '{text}' to bucket '{settings.bucket_name}'."
                    )

            try:
                key_response = client.get_object(settings.bucket_name, real_key)
                stored_content = key_response.data
            finally:
                key_response.close()
                key_response.release_conn()

            fastapi_logger.debug("Media served")
            return Response(stored_content, status_code=200, media_type="audio/opus")
        except Exception as e:
            fastapi_logger.error(f"{e}")
            return Response("Unable to serve content", status_code=500)

    return router
