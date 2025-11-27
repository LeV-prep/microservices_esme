FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY resource_service /app/resource_service

WORKDIR /app/resource_service

EXPOSE 7000

CMD ["python", "app.py"]
