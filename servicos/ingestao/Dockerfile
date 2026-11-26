FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY servicos/ ./servicos/
COPY documentos/ ./documentos/
ENV PORT=8001
CMD exec uvicorn servicos.ingestao.app:app --host ${HOST:-0.0.0.0} --port $PORT
