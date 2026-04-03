FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    postgresql-client

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]