FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 8000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8000} main:app"]
