import base64
import io
from threading import Lock

import minio.error
from fastapi import FastAPI
from fastapi import Response
from minio import Minio
from pydantic import BaseSettings

app = FastAPI()
BUCKET_NAME = "speech"
COUNTER_NAME = "counter"
AUDIO_FOLDER = "audio"

audio_lock = Lock()
counter_lock = Lock()


class Settings(BaseSettings):
    minio_url: str
    minio_access_key: str
    minio_secret_key: str
    gcp_counter_limit: int
    gcp_language: str
    gcp_voice_name: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        secrets_dir = "/run/secrets"


def object_exists(client: Minio, bucket_name: str, object_name: str) -> bool:
    print(f"Checking '{object_name}'")
    result = False
    try:
        client.stat_object(bucket_name, object_name)
        result = True
    except minio.error.S3Error as ex:
        print(ex)
    return result


# TODO fetch real audio
def obtain_audio(text: str) -> bytes:
    with open("example.mp3", "rb") as fp:
        content = fp.read()
    return content


@app.get("/")
async def read_root() -> dict:
    message = (
        f"Hello world! From FastAPI running on Uvicorn with Gunicorn. Using Python"
    )
    return {"message": message}


@app.get("/speech/")
async def speech(text: str = "Example") -> Response:
    real_key_suffix_bytes = base64.b64encode(text.encode("utf-8"))
    real_key_suffix = str(real_key_suffix_bytes, "utf-8")
    real_key = f"{AUDIO_FOLDER}/{real_key_suffix}"

    client: Minio = Minio(
        Settings().minio_url,
        access_key=Settings().minio_access_key,
        secret_key=Settings().minio_secret_key,
        secure=False,
    )

    # Make bucket if missing.
    found = client.bucket_exists(f"{BUCKET_NAME}")
    if not found:
        client.make_bucket(f"{BUCKET_NAME}")
    else:
        print(f"Bucket '{BUCKET_NAME}' already exists")

    with audio_lock:
        audio_object_exists = object_exists(client, BUCKET_NAME, real_key)
        if not audio_object_exists:
            content = obtain_audio(text)

            client.put_object(BUCKET_NAME, real_key, io.BytesIO(content), len(content))
            print(f"'Successfully uploaded object '{text}' to bucket '{BUCKET_NAME}'.")

    counter = 0
    with counter_lock:
        counter_object_exists = object_exists(client, BUCKET_NAME, COUNTER_NAME)
        if counter_object_exists:
            try:
                counter_response = client.get_object(BUCKET_NAME, COUNTER_NAME)
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
            client.put_object(BUCKET_NAME, COUNTER_NAME, counter_stream, len(counter_bytes))

    try:
        key_response = client.get_object(BUCKET_NAME, real_key)
        stored_content = key_response.data
    finally:
        key_response.close()
        key_response.release_conn()

    return Response(stored_content, status_code=200, media_type="audio/mp3")
