FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY servicos/ ./servicos/
CMD ["opentelemetry-instrument", "python", "-m", "servicos.mensageria.worker"]
