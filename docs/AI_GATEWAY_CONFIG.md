# 🤖 AI Gateway — Configuración

> Movido desde `AI_GATEWAY_CONFIG.md` (raíz) el 2026-08-11. Original fechado 2026-07-24; corregidas las rutas de archivo, que apuntaban a una estructura de carpetas (`src/agents/workers/macro/`, `src/agents/workers/news/`) que nunca existió en el repo — los workers viven planos en `src/agents/workers/`.

## Endpoints del AI Gateway

| Endpoint | Schema | Uso |
|----------|--------|-----|
| **finsight-chat** | `main.finsight_ai` | Chat / reasoning |
| **finsight-embeddings** | `main.finsight_ai` | Embeddings / RAG |

Formato de referencia usado en el código:
```python
ai_gateway_endpoint = "ai-gateway:/main.finsight_ai.finsight-chat"
```

`src/agents/base_agent.py` parsea este string (`catalog.schema.endpoint_name`) y llama a `WorkspaceClient.serving_endpoints.query(name=endpoint_name, ...)`.

## Workers que usan `finsight-chat`

Todo worker/agent que necesita razonamiento pasa por este endpoint. Estado real (ver [PROJECT_STATUS.md](./PROJECT_STATUS.md) para el detalle de qué supervisor está activo):

- `src/agents/workers/macro_data_worker.py`
- `src/agents/workers/regional_context_worker.py`
- `src/agents/workers/indicator_analysis_worker.py`
- `src/agents/workers/market_sentiment_worker.py`
- `src/agents/workers/event_detection_worker.py`
- `src/agents/workers/general_news_worker.py`
- `src/agents/workers/sector_news_worker.py`
- `src/agents/fundamental_agents.py` (los 4 ReAct agents del dominio Fundamental)

## `finsight-embeddings`

Reservado para RAG / búsqueda semántica — todavía no hay código en el repo que lo use (no hay vector search implementado, ver PROJECT_STATUS.md).

## Configurar un nuevo worker/agent

```python
from src.agents.base_agent import BaseAgent

class NuevoWorker(BaseAgent):
    def __init__(self):
        super().__init__(
            name="NuevoWorker",
            role="Worker Description",
            ai_gateway_endpoint="ai-gateway:/main.finsight_ai.finsight-chat",
            tools=TOOL_LIST,
            tool_functions=tool_functions,
            max_iterations=5,
            temperature=0.7
        )
```

## Testing

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

w = WorkspaceClient()
response = w.serving_endpoints.query(
    name="finsight-chat",
    messages=[ChatMessage(role=ChatMessageRole.USER, content="Test connection")]
)
print(response)
```

## Troubleshooting

**"Endpoint not found"** — confirmá que el endpoint existe en tu workspace:
```python
try:
    w.serving_endpoints.query(name="finsight-chat", messages=[...])
    print("✅ Endpoint funciona")
except Exception as e:
    print(f"❌ Error: {e}")
```

**"Permission denied"**
```sql
SHOW GRANTS ON SCHEMA main.finsight_ai;
```

## Archivos que referencian AI Gateway

- `src/agents/base_agent.py` — clase base que hace las llamadas
- `config/agent_configs.yaml` — configuración de modelos por supervisor/orchestrator
- `src/utils/config.py` — endpoints por defecto (`ai_gateway_synthesis`, `ai_gateway_analysis`, etc.)

---

**Fecha original:** 2026-07-24 · **Rutas corregidas:** 2026-08-11
