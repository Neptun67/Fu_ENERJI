FROM python:3.12-slim

WORKDIR /app

# Bağımlılıklar önce (katman önbelleği için)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Başlatmadan önce migration'ları uygula, sonra sunucuyu çalıştır.
# Railway $PORT'u enjekte eder; lokalde 8000'e düşer.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
