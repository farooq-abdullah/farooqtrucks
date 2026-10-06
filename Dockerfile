FROM node:22-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
COPY --from=frontend /build/frontend/dist ./frontend/dist
# Collect the Vite assets without requiring a deployment secret at build time.
RUN python backend/manage.py collectstatic --noinput
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "cd backend && exec gunicorn config.wsgi:application --workers 1 --threads 4 --timeout 180 --bind 0.0.0.0:${PORT:-8000}"]
