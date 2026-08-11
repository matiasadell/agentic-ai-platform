# 📊 Estado del Proyecto — FinSight AI / Agentic AI Platform

**Última actualización:** 2026-08-11 (auditoría contra el código real del repo)
**Estado:** 🟡 En desarrollo activo — múltiples patrones de agente coexisten, algunos módulos están rotos o duplicados

> Este documento reemplaza la versión anterior (fechada 2026-07-24), que describía una estructura de carpetas (`src/agents/workers/macro/`, `src/agents/workers/news/`, `src/mcp_servers/`) y una infraestructura (FastAPI, Docker, Neo4j, Redis, tests/) que **no existen en el código actual**. Todo lo de abajo está verificado contra el árbol de archivos real.

---

## 🎯 Qué es esto

Plataforma de agentes IA para análisis financiero, pensada para correr **nativamente en Databricks**:
- **Databricks AI Gateway** para el routing de LLM (`src/agents/base_agent.py`)
- **Unity Catalog Functions** como tools nativos (`src/agents/tools/uc_functions.py`, `notebooks/setup_uc_functions.ipynb`)
- **MLflow** (nativo de Databricks) para tracing
- **LangGraph** para orquestación de agentes/supervisors

No hay API REST, no hay contenedores, no hay tests automatizados en el repo hoy. Los `docker-compose`, `FastAPI`, `Neo4j`, `Redis`, `pytest tests/` que aparecían en versiones anteriores del README/QUICKSTART eran aspiracionales o de un diseño descartado — ver [DATABRICKS_NATIVE_ARCHITECTURE.md](./DATABRICKS_NATIVE_ARCHITECTURE.md), que documenta explícitamente por qué se abandonó ese enfoque híbrido.

---

## ✅ Lo que existe y compila (import-safe)

### Core
- **`src/agents/base_agent.py`** — Clase base abstracta: llama a Databricks AI Gateway vía `WorkspaceClient.serving_endpoints.query()`, loop de tool-calling, logging a MLflow. Requiere workspace de Databricks para correr (usa `databricks.sdk`, y tiene un `sys.path.insert` hardcodeado a `/Workspace/Users/matiasadell@hotmail.com` — solo funciona en ese workspace específico).
- **`src/utils/config.py`** — `Settings` (Pydantic) con las variables de entorno reales del proyecto; corresponde 1:1 con `.env.example`.
- **`src/utils/logging.py`**, **`src/utils/cache.py`** — utilidades de soporte.

### Dominio Macro — patrón "Workers" (data fetchers, sin razonamiento LLM propio salvo el que orquesta el supervisor)
- `src/agents/workers/macro_data_worker.py`
- `src/agents/workers/regional_context_worker.py`
- `src/agents/workers/indicator_analysis_worker.py`
- Supervisor: `src/agents/supervisors/macro_supervisor.py` ✅ (coordina los 3 workers, es el que se usa)

### Dominio News — patrón "Workers"
- `src/agents/workers/general_news_worker.py`
- `src/agents/workers/sector_news_worker.py`
- `src/agents/workers/market_sentiment_worker.py`
- `src/agents/workers/event_detection_worker.py`
- Supervisor: `src/agents/supervisors/news_supervisor.py` ✅ (coordina los 4 workers, es el que se usa)

### Dominio Fundamental — patrón distinto: "Agents" (ReAct, con LLM propio)
- `src/agents/fundamental_agents.py` — 4 `create_react_agent`: financial_statement, key_ratios, earnings, valuation
- Supervisor: `src/agents/supervisors/fundamental_supervisor_v2.py` ✅ (StateGraph secuencial de los 4 agents, es el que se usa)
- **`src/workers/fundamental.py`** — versión "worker" anterior de este mismo dominio (4 clases: `FinancialStatementWorker`, `KeyRatiosWorker`, `EarningsWorker`, `ValuationWorker`). Vive en `src/workers/`, un paquete paralelo a `src/agents/workers/` que no se usa desde ningún supervisor funcional — ver sección de problemas abajo.

### Schemas y validación
- `src/schemas/{base,fundamental,macro,news,validator}.py` — modelos Pydantic de respuesta por dominio.

### Config y notebooks
- `config/agent_configs.yaml` — configuración de orchestrator/supervisors (modelo, temperatura, timeouts).
- `notebooks/setup_uc_functions.ipynb` — `CREATE FUNCTION` de las **9** Unity Catalog functions: `get_gdp_data`, `get_inflation_data`, `get_unemployment_data`, `get_interest_rate`, `get_financial_news`, `get_regional_news`, `get_stock_prices`, `get_technical_indicators`, `detect_corporate_events`. (La documentación anterior, y el propio comentario de cabecera del archivo, decían "5 funciones" — desactualizado, quedó así al agregar las últimas 4 sin actualizar el comentario.)
- `notebooks/example_agent_usage.ipynb` — ejemplo de uso.
- `notebooks/8-multiagent.ipynb` — notebook standalone (patrón LangGraph de referencia con 3 agentes RAG); es la fuente del patrón que después se aplicó a `fundamental_agents.py`. Movido de la raíz del repo a `notebooks/` el 2026-08-11, y convertido de formato "Databricks notebook source" (`.py`) a `.ipynb` real junto con los otros dos archivos de esta carpeta.

---

## 🔴 Roto o inconsistente (verificado por import estático)

### 1. Tres supervisors `_langgraph.py` no importan
| Archivo | Import que falla |
|---|---|
| `src/agents/supervisors/macro_supervisor_langgraph.py` | `from src.workers.macro import (...)` — **`src/workers/macro.py` no existe** |
| `src/agents/supervisors/news_supervisor_langgraph.py` | `from src.workers.news import (...)` — **`src/workers/news.py` no existe** |
| `src/agents/supervisors/fundamental_supervisor_langgraph.py` | `from src.workers.fundamental import (...)` — este sí existe, pero nada más en el repo importa este supervisor tampoco |

Ninguno de los tres está referenciado desde otro módulo del repo. Son variantes abandonadas a medio migrar — probablemente el intento de portar `macro_supervisor.py` y `news_supervisor.py` al mismo patrón declarativo de `fundamental_supervisor_v2.py`, que se frenó antes de crear `src/workers/macro.py` / `src/workers/news.py`.

**Nota:** el `README.md` anterior afirmaba *"LangGraph Migration Complete... Total: 12 workers, 3 supervisors, ALL LangGraph!"* — eso es incorrecto; 2 de los 3 supervisors "LangGraph" no funcionan.

### 2. Dos jerarquías de "workers" paralelas
- `src/agents/workers/` (7 archivos, usados por `macro_supervisor.py` y `news_supervisor.py`)
- `src/workers/` (1 archivo, `fundamental.py`, usado solo por el supervisor `_langgraph` roto de fundamental)

Nombres coinciden en concepto pero no en ubicación ni convención; confunde a cualquiera que busque "el" paquete de workers.

### 3. Tres generaciones de supervisor para el dominio Fundamental
`fundamental_supervisor_langgraph.py` (roto), `fundamental_supervisor_v2.py` (el que funciona), y el patrón "workers" en `src/workers/fundamental.py` sin supervisor propio. No hay un `__init__.py` que declare cuál es el público — `src/agents/supervisors/__init__.py` está vacío.

### 4. `config/mcp_tools.yaml` referencia infraestructura eliminada
Apunta a `src/mcp_servers/financial_data_server.py`, que no existe — consistente con lo que dice `docs/DATABRICKS_NATIVE_ARCHITECTURE.md` (los MCP servers custom fueron descartados a favor de Unity Catalog Functions), pero el archivo de config nunca se borró ni actualizó.

### 5. Secretos hardcodeados en el repo (seguridad, no solo documentación)
- `notebooks/8-multiagent.ipynb` tiene una API key de Tavily en texto plano.
- `.env.example` tiene una API key de Financial Modeling Prep real (no un placeholder) en `FMP_API_KEY=`.

Esto contradice directamente [SECURITY_SETUP.md](./SECURITY_SETUP.md) ("Never hardcode API keys"). Ambas keys deberían rotarse y removerse del código, independientemente de cualquier otro cleanup.

---

## 📊 Cobertura real

| Dominio | Workers/Agents | Supervisor funcional |
|---|---|---|
| Macro | 3/3 (`macro_data`, `regional_context`, `indicator_analysis`) | ✅ `macro_supervisor.py` |
| News | 4/4 (`general_news`, `sector_news`, `market_sentiment`, `event_detection`) | ✅ `news_supervisor.py` |
| Fundamental | 4/4 agents (`fundamental_agents.py`) + 4 workers redundantes (`src/workers/fundamental.py`) | ✅ `fundamental_supervisor_v2.py` |
| Orchestrator (Nivel 1, `docs/ARCHITECTURE.md`) | — | ⬜ No implementado |

**No implementado:** Strategic Orchestrator (Nivel 1), RAG, knowledge graph (Neo4j), vector search, API endpoints, evaluation pipeline (RAGAS), guardrails, tests automatizados. Estos aparecen mencionados en README/ARCHITECTURE como visión de producto, no como código presente.

---

## 🗂️ Historial (changelog, consolidado desde IMPLEMENTATION_SUMMARY.md — 2026-07-30)

Implementación del patrón "Agents" para el dominio Fundamental, siguiendo el patrón de `notebooks/8-multiagent.ipynb`:
- ✅ `fundamental_agents.py` — 4 tools de LangChain + 4 ReAct agents
- ✅ `fundamental_supervisor_v2.py` — StateGraph secuencial: `financial_agent → ratios_agent → earnings_agent → valuation_agent`
- ✅ Documentación del cambio de paradigma Workers → Agents (ahora en el anexo de [ARCHITECTURE.md](./ARCHITECTURE.md))
- ⚠️ Pendiente en su momento: incompatibilidad de dependencias que requería reinicio de kernel para testing completo (no se sabe si sigue vigente — no verificable sin correr en Databricks)

Cleanup anterior (2026-07-24, referenciado en la versión previa de este doc): remoción de ~40 archivos no usados (`src/api/`, `src/evaluation/`, `src/graph/`, `src/guardrails/`, `src/tools/`, `src/rag/`, `tests/`, `data/`, `scripts/`), reducción de 516K a 248K.

Cleanup 2026-08-11 (esta sesión): eliminado `agentic-ai-platform.zip` + `unzip.py` (archivo comprimido del propio repo, commiteado por error) y `manifest.mf` (metadata de herramienta externa, no contenido real); documentación raíz consolidada en `docs/`; `8-multiagent.py` movido de la raíz a `notebooks/` y los tres archivos de `notebooks/` (`8-multiagent`, `example_agent_usage`, `setup_uc_functions`) convertidos de formato "Databricks notebook source" plano (`.py`/`.sql`) a `.ipynb` real.

---

## 🚀 Próximos pasos sugeridos

1. **Decidir y resolver** cuál supervisor de Fundamental es el canónico (`_v2` funciona; los otros dos deberían borrarse o completarse).
2. **Arreglar o borrar** `macro_supervisor_langgraph.py` y `news_supervisor_langgraph.py` (crear `src/workers/macro.py` y `src/workers/news.py`, o eliminar los tres archivos `_langgraph` y quedarse con el patrón "workers" que ya funciona).
3. **Unificar** `src/workers/` dentro de `src/agents/workers/` (o viceversa) para tener una sola jerarquía.
4. **Rotar y remover** las API keys hardcodeadas en `notebooks/8-multiagent.ipynb` y `.env.example`.
5. **Actualizar o borrar** `config/mcp_tools.yaml` (referencia código que ya no existe).
6. Recién después de eso: Strategic Orchestrator, RAG, evaluación, tests.

---

**Mantenido por:** Matias Adell
