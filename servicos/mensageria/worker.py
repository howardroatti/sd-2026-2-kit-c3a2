
"""
Worker de mensageria - C2.A2.

Consome documentos da fila Redis e envia
para o microsservico de ingestao.
"""

import json
import os
import time

import redis
import requests
from opentelemetry import trace
from opentelemetry.propagate import extract

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

URL_INGESTAO = os.getenv(
    "URL_INGESTAO",
    "http://localhost:8001"
)

NOME_FILA = "fila_ingestao"

tracer = trace.get_tracer("worker")

cliente_redis = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True
)


def processar_documentos(documentos):
    """Envia documentos para o servico de ingestao."""

    resposta = requests.post(
        f"{URL_INGESTAO}/indexar",
        json=documentos,
        timeout=15
    )

    resposta.raise_for_status()

    print("Documentos indexados:", resposta.json(), flush=True)


def iniciar_worker():
    print("Worker de ingestao iniciado.", flush=True)

    while True:
        try:
            print("Aguardando documentos...", flush=True)

            resultado = cliente_redis.blpop(
                NOME_FILA,
                timeout=5
            )

            if resultado is None:
                continue

            _, mensagem = resultado
            msg = json.loads(mensagem)
            if isinstance(msg, list):
                msg = {"documentos": msg}

            try:
                with tracer.start_as_current_span(
                    "processar_documentos",
                    context=extract(msg.get("trace", {}))
                ):
                    processar_documentos(msg["documentos"])

            except requests.RequestException as erro:
                print("Erro na ingestao:", erro, flush=True)

                # Recoloca a mensagem na fila.
                cliente_redis.rpush(NOME_FILA, mensagem)
                time.sleep(3)

        except redis.RedisError as erro:
            print("Erro de conexao com Redis:", erro, flush=True)
            time.sleep(3)

        except (ValueError, TypeError, KeyError, AttributeError) as erro:
            print("Mensagem invalida:", erro, flush=True)


if __name__ == "__main__":
    iniciar_worker()
