FROM python:3.14-slim AS builder

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


FROM python:3.14-slim

RUN apt-get update && apt-get install -y \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.14 /usr/local/lib/python3.14
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app

EXPOSE 8900
