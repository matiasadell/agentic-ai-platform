# 🤖 Guía de Workers y Agents

> Reescrito el 2026-08-11. La versión anterior (`WORKER_VERSIONS_GUIDE.md`, raíz) describía un sistema de "2 versiones por worker" (`macro_data_worker.py` + `macro_data_worker_simple.py`, `market_sentiment.py` + `market_sentiment_simple.py`) que **no existe en el repo** — no hay un solo archivo `*_simple.py` en todo el proyecto, y `market_sentiment.py` (sin `_worker`) tampoco existe, el archivo real es `market_sentiment_worker.py`. Este documento describe la estructura real actual. Ver [PROJECT_STATUS.md](./PROJECT_STATUS.md) para el detalle de qué está roto.
>
> **Corrección (2026-08-11, verificada leyendo las 7 clases directamente):** la primera versión de este documento decía que los workers de Macro/News "extienden `BaseAgent`". Eso es incorrecto — ninguno de los 7 lo hace. Son clases standalone que instancian `ChatDatabricks` directamente. `BaseAgent` existe y sí está bien conectado al AI Gateway, pero no lo usa nada del pipeline que realmente funciona.

## Resumen

Hay **dos patrones distintos** conviviendo en el repo, no dos versiones del mismo worker — y ninguno de los dos pasa por `BaseAgent`/AI Gateway:

1. **Workers** (`src/agents/workers/`) — usados por los dominios Macro y News. Clases standalone (no extienden nada), instancian `ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")` directamente — **Llama 3.3 70B** vía Databricks Model Serving, sin pasar por el AI Gateway.
2. **Agents ReAct** (`src/agents/fundamental_agents.py`) — usados por el dominio Fundamental. Usan `create_react_agent` de LangGraph con `init_chat_model("openai:gpt-4o-mini")` — **OpenAI GPT-4o-mini** directo, ni Databricks ni AI Gateway de por medio.

Además existe `src/workers/fundamental.py`, una tercera variante (patrón "worker" pero para Fundamental) que solo es importada por un supervisor roto — ver más abajo.

## Workers (dominio Macro y News)

Todos en `src/agents/workers/`. **Ninguno extiende `BaseAgent`** pese a lo que decía la versión anterior de este documento — son clases standalone:

| Worker | Archivo | Dominio |
|---|---|---|
| MacroDataWorker | `macro_data_worker.py` | Macro |
| RegionalContextWorker | `regional_context_worker.py` | Macro |
| IndicatorAnalysisWorker | `indicator_analysis_worker.py` | Macro |
| MarketSentimentWorker | `market_sentiment_worker.py` | News |
| EventDetectionWorker | `event_detection_worker.py` | News |
| GeneralNewsWorker | `general_news_worker.py` | News |
| SectorNewsWorker | `sector_news_worker.py` | News |

Características comunes:
- Instancian `ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")` directamente en `__init__` — **no** usan el AI Gateway (`finsight-chat`) que `docs/AI_GATEWAY_CONFIG.md` documenta como el mecanismo central
- Tool calling manual (no vía `BaseAgent.register_tool`)
- Sin logging a MLflow (eso solo existe en `BaseAgent.process()`, que no usan)

Ejemplo de uso:
```python
from src.agents.workers.macro_data_worker import MacroDataWorker

worker = MacroDataWorker()
result = worker.process(user_query="What's the GDP and inflation of USA?")
```

Coordinados por sus respectivos supervisors:
```python
from src.agents.supervisors.macro_supervisor import MacroSupervisor
from src.agents.supervisors.news_supervisor import NewsSupervisor
```

## Agents (dominio Fundamental)

`src/agents/fundamental_agents.py` — 4 `create_react_agent` de LangGraph, cada uno con su propio LLM y tools de LangChain (`@tool`), siguiendo el patrón de `notebooks/8-multiagent.ipynb`. No extienden `BaseAgent`; no pasan por el mismo mecanismo de AI Gateway que los workers de arriba.

```python
from src.agents.fundamental_agents import (
    create_financial_statement_agent,
    create_key_ratios_agent,
    create_earnings_agent,
    create_valuation_agent,
)
```

Coordinados por:
```python
from src.agents.supervisors.fundamental_supervisor_v2 import get_fundamental_supervisor
```

Ver el anexo de [ARCHITECTURE.md](./ARCHITECTURE.md) para la explicación completa de por qué este dominio usa un patrón distinto (fue una migración intencional de Workers → Agents, documentada en su momento).

## `src/workers/fundamental.py` — variante no usada, huérfana

Este archivo implementa el dominio Fundamental como 4 clases "worker" clásicas (`FinancialStatementWorker`, `KeyRatiosWorker`, `EarningsWorker`, `ValuationWorker`), en paralelo a `fundamental_agents.py`. Solo lo importa `fundamental_supervisor_langgraph.py`, que a su vez no es usado por nada más en el repo (ver PROJECT_STATUS.md).

**Recomendación:** decidir si este archivo se elimina (si `fundamental_supervisor_v2.py` + `fundamental_agents.py` es el camino canónico) o si se completa la migración del supervisor `_langgraph`. Mantener las tres variantes vivas sin uso activo es la causa principal de la confusión que tenía este documento antes.

## Al crear un worker/agent nuevo

- Si es para Macro o News (o sigue ese patrón): el precedente real es una clase standalone con `ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")`, no `BaseAgent`. Antes de copiar ese patrón vale la pena decidir si en realidad se quiere migrar todo a `BaseAgent`/AI Gateway (que sí tiene MLflow logging y gobierna el endpoint centralmente) — seguir agregando workers que bypasean el Gateway hace más costosa esa migración después.
- Si es para Fundamental (o un dominio nuevo que use ReAct agents en vez de workers): seguir el patrón de `fundamental_agents.py` — pero notar que usa OpenAI directo, no Databricks.
- No crear variantes `_simple` "para testing" salvo que realmente se vayan a mantener — la guía anterior recomendaba esto y terminó describiendo archivos que nunca se creían o que se borraron sin actualizar la doc.

---

**Reescrito:** 2026-08-11
