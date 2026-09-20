FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt

COPY backend ./backend
COPY frontend ./frontend

RUN useradd --create-home appuser
USER appuser

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} backend.app:app"]
