FROM python:3.12-slim

# nmap is required for real network scans. Raw-socket / OS-detection
# privileges are granted at the container level via NET_ADMIN/NET_RAW
# capabilities in docker-compose.yml, rather than running as root.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /app/data/reports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
