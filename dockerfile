# Dockerfile (оставьте его пустым или добавьте базовый образ python)
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .