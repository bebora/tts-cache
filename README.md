# tts-cache
## Local development
Create a `.env` file with the following properties
```ini
MINIO_URL="127.0.0.1:9000"
MINIO_ACCESS_KEY=REPLACEME
MINIO_SECRET_KEY=REPLACEME
GCP_COUNTER_LIMIT=1000000
GCP_LANGUAGE=de
GCP_VOICE_NAME="de-DE-Wavenet-B"
```
Create a folder `/mnt/minio` and start minio with this command
```bash
docker run -p 9000:9000 \
    -e "MINIO_ACCESS_KEY=REPLACEME" \
    -e "MINIO_SECRET_KEY=REPLACEME" \
    -v /mnt/minio:/data \
    minio/minio server /data
```
You can see the minio web interface at http://127.0.0.1:9000/minio/

Launch the FastAPI server from the main directory with uvicorn
```bash
uvicorn --factory app.app:create_app --reload
```
or with Gunicorn
```bash
gunicorn -k uvicorn.workers.UvicornWorker "app.app:create_app()"
```
