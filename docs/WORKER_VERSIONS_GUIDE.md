# 🤖 Guía de Workers y Agents

> Reescrito el 2026-08-11. La versión anterior (`WORKER_VERSIONS_GUIDE.md`, raíz) describía un sistema de "2 versiones por worker" (`macro_data_worker.py` + `macro_data_worker_simple.py`, `market_sentiment.py` + `market_sentiment_simple.py`) que **no existe en el repo** — no hay un solo archivo `*_simple.py` en todo el proyecto, y `market_sentiment.py` (sin `_worker`) tampoco existe, el archivo real es `market_sentiment_worker.py`. Este documento describe la estructura real actual. Ver [PROJECT_STATUS.md](./PROJECT_STATUS.md) para el detalle de qué está roto.

## Resumen

Hay **dos patrones distintos** conviviendo en el repo, no dos versiones del mismo worker:

1. **Workers** (`src/agents/workers/`) — usados por los dominios Macro y News. Extienden `BaseAgent`, pasan por AI Gateway.
2. **Agents ReAct** (`src/agents/fundamental_agents.py`) — usados por el dominio Fundamental. Usan `create_react_agent` de LangGraph directamente, no extienden `BaseAgent`.

Además existe `src/workers/fundamental.py`, una tercera variante (patrón "worker" pero para Fundamental) que solo es importada por un supervisor roto — ver más abajo.

## Workers (dominio Macro y News)

Todos en `src/agents/workers/`, todos extienden `BaseAgent` (`src/agents/base_agent.py`):

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
- Extienden `BaseAgent` → usan AI Gateway (`finsight-chat`) para razonar
- Tool calling vía `tool_functions` pasados al constructor
- Logging a MLflow vía `BaseAgent.process()`

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

- Si es para Macro o News (o sigue ese patrón): extender `BaseAgent`, ponerlo en `src/agents/workers/`, agregarlo al supervisor correspondiente.
- Si es para Fundamental (o un dominio nuevo que use ReAct agents en vez de workers): seguir el patrón de `fundamental_agents.py`.
- No crear variantes `_simple` "para testing" salvo que realmente se vayan a mantener — la guía anterior recomendaba esto y terminó describiendo archivos que nunca se creían o que se borraron sin actualizar la doc.

---

**Reescrito:** 2026-08-11
