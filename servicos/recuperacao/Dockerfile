FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY servicos/ ./servicos/
ENV PORT=8002
CMD exec uvicorn servicos.recuperacao.app:app --host ${HOST:-0.0.0.0} --port $PORT
