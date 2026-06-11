FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app
ENV RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

EXPOSE 8009

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8009"]