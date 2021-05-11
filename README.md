# tts-cache
## Local development
Create a `.env` file with the following properties
```ini
MINIO_URL="127.0.0.1:9000"
MINIO_ACCESS_KEY=REPLACEME
MINIO_SECRET_KEY=REPLACEME
GCP_COUNTER_LIMIT=500000
GCP_LANGUAGE="de-DE"
GCP_VOICE_NAME="de-DE-Wavenet-D"
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google/application/credentials.json
AUDIO_EXPIRY=365
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
## Docker Compose deployment
Create a `.env.docker` file with the following properties
```ini
MINIO_URL=minio:9000
MINIO_ACCESS_KEY=REPLACEME
MINIO_SECRET_KEY=REPLACEME
GCP_COUNTER_LIMIT=500000
GCP_LANGUAGE=de-DE
GCP_VOICE_NAME=de-DE-Wavenet-D
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/google_json
AUDIO_EXPIRY=365
```
Get your GCP credentials enabled to use the Text-To-Speech API and set their location (on the host machine) in the `docker-compose.yml` in the `google_json` secret.

Create a folder `/mnt/minio` or change the directory in the `docker-compose.yml` file to a directory of you choosing.

Start the app with
```bash
docker-compose up -d
```
The service will listen at port 22243 (*cache* in t9).