FROM python:3.12-slim

WORKDIR /app

# Dependencies first, for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Apply migrations before starting, then run the server.
# Railway injects $PORT; falls back to 8000 locally.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
