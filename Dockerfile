# Playwright image version must match the playwright pin in requirements.txt
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
RUN apt-get update && apt-get install -y --no-install-recommends xvfb && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dashboard ./dashboard
COPY automation ./automation
ENV DATA_DIR=/data
EXPOSE 8000
CMD ["uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8000"]
