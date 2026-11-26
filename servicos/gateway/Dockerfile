FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY servicos/ ./servicos/
ENV PORT=8000
CMD exec opentelemetry-instrument uvicorn servicos.gateway.app:app --host ${HOST:-0.0.0.0} --port $PORT
