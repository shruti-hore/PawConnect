FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system --gid 10001 pawconnect \
    && useradd --system --uid 10001 --gid pawconnect --home-dir /app pawconnect

COPY --chown=pawconnect:pawconnect app ./app
COPY --chown=pawconnect:pawconnect migrations ./migrations

USER pawconnect

EXPOSE 5000

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:5000 --workers ${WEB_CONCURRENCY:-2} --access-logfile - --error-logfile - 'app:create_app()'"]
