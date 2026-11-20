# Worker de fila

Worker do C1.A2: consome a fila `tarefas` no Redis, executa o modelo e grava o resultado.
Retentativa (3x) e fila de descarte `tarefas_dead_letter`.

Rodar: `python -m app.worker`
