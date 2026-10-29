FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Credentials and database settings come from the environment at run time:
#   docker run --rm -e SPOTIFY_CLIENT_ID=... -e SPOTIFY_CLIENT_SECRET=... -e DB_HOST=... trending-songs-finder
ENTRYPOINT ["python", "main.py"]
CMD ["fetch"]
