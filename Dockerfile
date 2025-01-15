FROM python:3.12.8-slim

RUN apt update && apt install -y r-base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app/
COPY app/.env app/

CMD ["python", "app/main.py"]
