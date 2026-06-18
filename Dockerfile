# Build
FROM python:3.12-slim AS builder

WORKDIR /bot

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Runtime
FROM python:3.12-slim

WORKDIR /bot

COPY --from=builder /install /usr/local
COPY . .

RUN useradd -m botuser
USER botuser

ENTRYPOINT ["python", "bot.py"]