FROM python:3.11-slim AS builder
WORKDIR /install
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

FROM python:3.11-slim
WORKDIR /code
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr libgl1 poppler-utils curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install/deps /usr/local
COPY ./app /code/app
# Models are mounted as a volume — not baked into the image
ENV PYTHONUNBUFFERED=1
# Single worker: LLM singleton is not multiprocess-safe
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]