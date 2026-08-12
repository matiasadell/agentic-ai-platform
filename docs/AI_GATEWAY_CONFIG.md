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

## ⚠️ Workers que *deberían* usar `finsight-chat` — pero no lo hacen (verificado 2026-08-11)

Este documento (en su versión original) decía que todos estos workers pasan por `finsight-chat`. **Falso, verificado leyendo el código directamente.** Ninguno de los dos patrones reales del repo pasa por el AI Gateway:

- Los 7 workers de Macro/News instancian `ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")` directamente — llaman al Model Serving endpoint de **Llama 3.3 70B** por nombre, sin pasar por `finsight-chat`/AI Gateway:
  - `src/agents/workers/macro_data_worker.py`, `regional_context_worker.py`, `indicator_analysis_worker.py`, `market_sentiment_worker.py`, `event_detection_worker.py`, `general_news_worker.py`, `sector_news_worker.py`
  - Sus supervisores (`macro_supervisor.py`, `news_supervisor.py`) hacen lo mismo para su propio LLM de routing/síntesis.
- `src/agents/fundamental_agents.py` (los 4 ReAct agents del dominio Fundamental) usa `init_chat_model("openai:gpt-4o-mini")` — **OpenAI GPT-4o-mini** directo con una API key de OpenAI, ni Databricks ni AI Gateway de por medio.

`BaseAgent` (la única clase del repo que realmente llama a `finsight-chat` vía `ai_gateway_endpoint`) no es extendida por ninguno de los workers/agents de arriba — existe pero está huérfana. Ver [PROJECT_STATUS.md](./PROJECT_STATUS.md) para el resto del inventario de módulos huérfanos/duplicados.

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
