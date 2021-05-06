import io

from fastapi.logger import logger as fastapi_logger
from minio import Minio
from minio.commonconfig import Tags
from minio.error import S3Error
from pydantic import BaseModel


class MinioCounterTags(BaseModel):
    working_month: str


class AudioFetchException(Exception):
    pass


def object_exists(client: Minio, bucket_name: str, object_name: str) -> bool:
    fastapi_logger.debug(f"Checking '{object_name}'")
    result = False
    try:
        client.stat_object(bucket_name, object_name)
        result = True
    except S3Error as ex:
        if ex.code == "NoSuchKey":
            fastapi_logger.debug(ex)
        else:
            fastapi_logger.error(ex)
    return result


# TODO fetch real audio
def obtain_audio(text: str) -> bytes:
    with open("example.mp3", "rb") as fp:
        content = fp.read()
    return content


def get_counter_value(
    client: Minio, bucket_name: str, counter_name: str, working_month: str
) -> int:
    tags: MinioCounterTags = client.get_object_tags(bucket_name, counter_name)
    # Reset counter if a new month started
    if tags is None:
        tags = MinioCounterTags(working_month="")
    if tags.working_month != working_month:
        new_tags = Tags.new_object_tags()
        new_tags.working_month = working_month
        client.set_object_tags(bucket_name, counter_name, new_tags)
        counter_stream = io.BytesIO(b"0")
        client.put_object(bucket_name, counter_name, counter_stream, len(b"0"))
        return 0
    else:
        try:
            counter_response = client.get_object(bucket_name, counter_name)
            counter = int(counter_response.data)
        finally:
            counter_response.close()
            counter_response.release_conn()
        return counter
