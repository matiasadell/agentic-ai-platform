# 📊 Estado del Proyecto — FinSight AI / Agentic AI Platform

**Última actualización:** 2026-08-11 (auditoría contra el código real del repo)
**Estado:** 🟡 En desarrollo activo — múltiples patrones de agente coexisten y hay módulos duplicados/huérfanos, pero (desde el 2026-08-11) todos los imports de `src/` son válidos

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
- **`src/agents/base_agent.py`** — Clase base abstracta: llama a Databricks AI Gateway vía `WorkspaceClient.serving_endpoints.query()`, loop de tool-calling, logging a MLflow. Requiere workspace de Databricks para *correr* (usa `databricks.sdk`) — pero desde el 2026-08-11 al menos *importa* en cualquier entorno (antes tenía un import roto, ver más abajo).
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

## ✅ Corregido el 2026-08-11 (import audit + fixes)

Se corrió un chequeo estático de imports contra los 32 archivos `.py` de `src/` (AST, resolviendo cada `from src.X import Y` contra los nombres reales del módulo destino), y se arreglaron todos los hallazgos:

1. **`macro_supervisor_langgraph.py` y `news_supervisor_langgraph.py` estaban rotos** — importaban `src.workers.macro` / `src.workers.news`, que no existen, con nombres de clase (`RegionalDataWorker`, `TechnicalIndicatorWorker`, `EconomicEventWorker`, `NewsAnalysisWorker`, `CorporateEventWorker`) que tampoco correspondían a ninguna clase real del repo. Reescritos para usar las clases reales de `src.agents.workers.*` y sus firmas reales (verificadas contra `macro_supervisor.py` / `news_supervisor.py`, que documentan los parámetros exactos en su routing prompt). El nodo `event_worker` de `macro_supervisor_langgraph.py` se eliminó — no existe ningún worker de "eventos macroeconómicos" (FOMC/Fed) en el repo; `EventDetectionWorker` es del dominio News (eventos corporativos), ya usado ahí. Ambos archivos ahora importan y compilan correctamente (verificado con AST + `py_compile`).
2. **`fundamental_supervisor_langgraph.py`** — confirmado que sus imports y llamadas a métodos son correctos (no estaba roto, solo huérfano). Sigue sin ser importado por nada más en el repo; ver "Próximos pasos".
3. **`src/agents/base_agent.py` tenía el import más grave de todos, no detectado en la primera pasada**: hacía `sys.path.insert(0, '/Workspace/Users/matiasadell@hotmail.com')` y `from agentic_ai_platform.src.utils.config import Settings` — un prefijo de paquete (`agentic_ai_platform.`) que no usa ningún otro archivo del repo, más una ruta hardcodeada a un workspace de Databricks específico. Como `BaseAgent` es la clase padre de los 7 workers, esto rompía el import de toda la capa Workers fuera de ese workspace exacto. Corregido a `from src.utils.config import Settings`, igual que el resto del código.
4. **`src/agents/tools/` y `src/workers/` no tenían `__init__.py`** (a diferencia de todos sus paquetes hermanos). No rompía imports corriendo desde el repo (namespace packages de Python 3), pero `pyproject.toml` usa `[tool.setuptools.packages.find]` (no `find_namespace`), que solo descubre paquetes con `__init__.py` — un `pip install .` real probablemente excluía `uc_functions.py` y `src/workers/fundamental.py` del paquete instalado. Se agregaron ambos `__init__.py`.
5. **Docstrings con rutas de import inexistentes**: `general_news_worker.py` y `sector_news_worker.py` mostraban `from src.agents.workers.news.general_news_worker import ...` (un subpaquete `workers/news/` que nunca existió). Corregidas a la ruta real y plana.
6. **`src/schemas/__init__.py` no re-exportaba los schemas de Fundamental** (`FinancialStatementResponse`, `KeyRatiosResponse`, `EarningsResponse`, `ValuationResponse`), a diferencia de Macro y News. Agregados para simetría.

## 🔴 Sigue roto o inconsistente

### 1. Dos jerarquías de "workers" paralelas
- `src/agents/workers/` (7 archivos, usados por `macro_supervisor.py` y `news_supervisor.py`, y ahora también por los dos `_langgraph.py` recién arreglados)
- `src/workers/` (1 archivo, `fundamental.py`, usado solo por `fundamental_supervisor_langgraph.py`, que sigue huérfano)

Nombres coinciden en concepto pero no en ubicación ni convención; confunde a cualquiera que busque "el" paquete de workers.

### 2. Tres generaciones de supervisor para el dominio Fundamental
`fundamental_supervisor_langgraph.py` (funciona pero huérfano — nada lo importa), `fundamental_supervisor_v2.py` (el que se usa), y el patrón "workers" en `src/workers/fundamental.py` sin supervisor propio. No hay un `__init__.py` que declare cuál es el público — `src/agents/supervisors/__init__.py` está vacío.

### 3. `config/mcp_tools.yaml` referencia infraestructura eliminada
Apunta a `src/mcp_servers/financial_data_server.py`, que no existe — consistente con lo que dice `docs/DATABRICKS_NATIVE_ARCHITECTURE.md` (los MCP servers custom fueron descartados a favor de Unity Catalog Functions), pero el archivo de config nunca se borró ni actualizó.

### 4. Secretos hardcodeados en el repo (seguridad, no solo documentación)
- `notebooks/8-multiagent.ipynb` tiene una API key de Tavily en texto plano.
- `.env.example` tiene una API key de Financial Modeling Prep real (no un placeholder) en `FMP_API_KEY=`.

Esto contradice directamente [SECURITY_SETUP.md](./SECURITY_SETUP.md) ("Never hardcode API keys"). Ambas keys deberían rotarse y removerse del código, independientemente de cualquier otro cleanup.

---

## 📊 Cobertura real

| Dominio | Workers/Agents | Supervisor funcional (usado) | Variante LangGraph declarativa |
|---|---|---|---|
| Macro | 3/3 (`macro_data`, `regional_context`, `indicator_analysis`) | ✅ `macro_supervisor.py` | ✅ `macro_supervisor_langgraph.py` (import-safe desde 2026-08-11, no usado por nada más todavía) |
| News | 4/4 (`general_news`, `sector_news`, `market_sentiment`, `event_detection`) | ✅ `news_supervisor.py` | ✅ `news_supervisor_langgraph.py` (ídem) |
| Fundamental | 4/4 agents (`fundamental_agents.py`) + 4 workers redundantes (`src/workers/fundamental.py`) | ✅ `fundamental_supervisor_v2.py` | ✅ `fundamental_supervisor_langgraph.py` (siempre fue import-safe, ídem) |
| Orchestrator (Nivel 1, `docs/ARCHITECTURE.md`) | — | ⬜ No implementado | — |

**No implementado:** Strategic Orchestrator (Nivel 1), RAG, knowledge graph (Neo4j), vector search, API endpoints, evaluation pipeline (RAGAS), guardrails, tests automatizados. Estos aparecen mencionados en README/ARCHITECTURE como visión de producto, no como código presente.

---

## 🗂️ Historial (changelog, consolidado desde IMPLEMENTATION_SUMMARY.md — 2026-07-30)

Implementación del patrón "Agents" para el dominio Fundamental, siguiendo el patrón de `notebooks/8-multiagent.ipynb`:
- ✅ `fundamental_agents.py` — 4 tools de LangChain + 4 ReAct agents
- ✅ `fundamental_supervisor_v2.py` — StateGraph secuencial: `financial_agent → ratios_agent → earnings_agent → valuation_agent`
- ✅ Documentación del cambio de paradigma Workers → Agents (ahora en el anexo de [ARCHITECTURE.md](./ARCHITECTURE.md))
- ⚠️ Pendiente en su momento: incompatibilidad de dependencias que requería reinicio de kernel para testing completo (no se sabe si sigue vigente — no verificable sin correr en Databricks)

Cleanup anterior (2026-07-24, referenciado en la versión previa de este doc): remoción de ~40 archivos no usados (`src/api/`, `src/evaluation/`, `src/graph/`, `src/guardrails/`, `src/tools/`, `src/rag/`, `tests/`, `data/`, `scripts/`), reducción de 516K a 248K.

Cleanup 2026-08-11 (esta sesión): eliminado `agentic-ai-platform.zip` + `unzip.py` (archivo comprimido del propio repo, commiteado por error) y `manifest.mf` (metadata de herramienta externa, no contenido real); documentación raíz consolidada en `docs/`; `8-multiagent.py` movido de la raíz a `notebooks/` y los tres archivos de `notebooks/` (`8-multiagent`, `example_agent_usage`, `setup_uc_functions`) convertidos de formato "Databricks notebook source" plano (`.py`/`.sql`) a `.ipynb` real; auditoría estática de imports sobre los 32 archivos de `src/` y fixes aplicados — ver "✅ Corregido el 2026-08-11" arriba (import roto en `base_agent.py`, dos supervisors `_langgraph` reescritos, `__init__.py` faltantes, docstrings y exports de schemas corregidos).

---

## 🚀 Próximos pasos sugeridos

1. **Decidir cuál supervisor es el canónico por dominio** ahora que los tres `_langgraph.py` importan correctamente: quedarse con la versión manual (`macro_supervisor.py`, `news_supervisor.py`, `fundamental_supervisor_v2.py`) o migrar a la declarativa (`*_langgraph.py`) y borrar la otra. Tenerlas todas vivas y sin uso es la causa original de la confusión.
2. **Unificar** `src/workers/` dentro de `src/agents/workers/` (o viceversa) para tener una sola jerarquía.
3. **Rotar y remover** las API keys hardcodeadas en `notebooks/8-multiagent.ipynb` y `.env.example`.
4. **Actualizar o borrar** `config/mcp_tools.yaml` (referencia código que ya no existe).
5. Recién después de eso: Strategic Orchestrator, RAG, evaluación, tests.

---

**Mantenido por:** Matias Adell
