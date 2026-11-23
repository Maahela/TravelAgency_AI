FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user (data/ and logs/ are mounted volumes)
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /app/data /app/logs \
 && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/admin_dashboard/backend

EXPOSE 4005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4005"]