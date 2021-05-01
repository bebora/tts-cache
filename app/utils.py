from minio import Minio
from minio.error import S3Error


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
