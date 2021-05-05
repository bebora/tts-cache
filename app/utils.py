import io

from minio import Minio
from minio.error import S3Error
from pydantic import BaseModel


class MinioCounterTags(BaseModel):
    working_month: str


def object_exists(client: Minio, bucket_name: str, object_name: str) -> bool:
    print(f"Checking '{object_name}'")
    result = False
    try:
        client.stat_object(bucket_name, object_name)
        result = True
    except S3Error as ex:
        print(ex)
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
    if tags.working_month != working_month:
        tags.working_month = working_month
        client.set_object_tags(bucket_name, counter_name, tags)
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
