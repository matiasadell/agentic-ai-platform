# 📊 Estado del Proyecto — FinSight AI / Agentic AI Platform

**Última actualización:** 2026-08-11 (auditoría contra el código real del repo)
**Estado:** 🟡 En desarrollo activo — múltiples patrones de agente coexisten y hay módulos duplicados/huérfanos, pero (desde el 2026-08-11) todos los imports de `src/` son válidos

> Este documento reemplaza la versión anterior (fechada 2026-07-24), que describía una estructura de carpetas (`src/agents/workers/macro/`, `src/agents/workers/news/`, `src/mcp_servers/`) y una infraestructura (FastAPI, Docker, Neo4j, Redis, tests/) que **no existen en el código actual**. Todo lo de abajo está verificado contra el árbol de archivos real.

---

## 🎯 Qué es esto

Plataforma de agentes IA para análisis financiero, pensada para correr **nativamente en Databricks**:
- **Unity Catalog Functions** como tools nativos (`src/agents/tools/uc_functions.py`, `notebooks/setup_uc_functions.ipynb`)
- **LangGraph** para orquestación de agentes/supervisors
- Databricks AI Gateway y MLflow **existen en el repo** (`src/agents/base_agent.py`) pero — ver sección siguiente — no los usa el pipeline que realmente funciona hoy.

No hay API REST, no hay contenedores, no hay tests automatizados en el repo hoy. Los `docker-compose`, `FastAPI`, `Neo4j`, `Redis`, `pytest tests/` que aparecían en versiones anteriores del README/QUICKSTART eran aspiracionales o de un diseño descartado — ver [DATABRICKS_NATIVE_ARCHITECTURE.md](./DATABRICKS_NATIVE_ARCHITECTURE.md), que documenta explícitamente por qué se abandonó ese enfoque híbrido.

---

## 🤖 Qué LLM se usa realmente (verificado 2026-08-11)

No hay un solo LLM ni un solo mecanismo de acceso — hay dos, ninguno pasa por el AI Gateway que la documentación (`docs/AI_GATEWAY_CONFIG.md`) describe como el punto de entrada central:

| Dominio | LLM real | Cómo se llama |
|---|---|---|
| Macro, News (los 7 workers + sus 2 supervisors) | **Llama 3.3 70B Instruct** | `ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")` — Databricks Model Serving directo, sin AI Gateway |
| Fundamental (4 ReAct agents + supervisor) | **OpenAI GPT-4o-mini** | `init_chat_model("openai:gpt-4o-mini")` — OpenAI directo con API key, ni Databricks ni AI Gateway |

`BaseAgent` (`src/agents/base_agent.py`) es la única clase del repo que sí llama al AI Gateway (`ai-gateway:/main.finsight_ai.finsight-chat`) con logging a MLflow — pero **nada la extiende ni la importa** fuera de un ejemplo en la documentación. Existe, importa correctamente (ver el fix de import más abajo), pero está completamente desconectada del código que efectivamente corre. La primera versión de este documento y de `docs/WORKER_VERSIONS_GUIDE.md` decían que los 7 workers "extienden `BaseAgent`" — es incorrecto, corregido en ambos documentos.

Esto significa que hoy no hay governance centralizado de LLM (rate limits, cost tracking, un solo lugar para cambiar de modelo) pese a que el README y `docs/AI_GATEWAY_CONFIG.md` lo describen como ya configurado — es una brecha real entre lo documentado como arquitectura objetivo y lo que el código hace.

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

### Data Engineering — pipeline de ingesta batch de yfinance (nuevo, 2026-08-11)
- `config/data_ingest/daily_batch_config.json` — lista de tickers a ingestar + `start_date` incremental por ticker (`null` = nunca ingestado).
- `config/data_ingest/catalog_config.json` — catálogo destino (`{"catalog": "main"}`), config separada de `src/utils/config.py`/`.env` a propósito (superficie de config plana para el lado de data engineering, no Pydantic).
- `notebooks/data/data_ingest/orchestrator.ipynb` — lee ambos configs, hace fan-out a `worker.ipynb` en paralelo vía `ThreadPoolExecutor` + `dbutils.notebook.run`. `dbutils` se usa como global del notebook, sin import explícito. Parsea el JSON que devuelve cada worker (`json.loads(result)`) y actualiza el `start_date` de ese ticker con `result["last_date"]` cuando `result["ingestionStatus"] == 1` — el orchestrator no vuelve a consultar la tabla para saber la fecha. Sin try/except alrededor de `future.result()`: el contrato del worker (siempre sale con JSON válido, éxito o falla) hace innecesario ese manejo defensivo — si algo lo rompe (timeout, infraestructura), es un bug a arreglar, no una condición a tolerar en silencio.
- `notebooks/data/data_ingest/worker.ipynb` — por ticker: `yfinance.download` (diario, `period="max"` en la primera corrida o `start=start_date` en corridas incrementales), calcula `MAX(date)` sobre el propio pandas DataFrame en memoria (no una query aparte a la tabla ya escrita), escribe en `{catalog}.yfinance.{ticker_sanitizado}` (Delta, append-only), y sale con `dbutils.notebook.exit(json.dumps(...))`: `{"ingestionStatus": 1, "last_date": "YYYY-MM-DD"}` si tuvo éxito, `{"ingestionStatus": 0, "last_date": None}` si falló. Import de `yfinance` con fallback: `try: import yfinance except ImportError: pip install yfinance; import yfinance` — sin `%pip`/`restartPython`, portable fuera de Databricks también.
- Sin tests automatizados de esto todavía — solo se verificó que ambos `.ipynb` son JSON válido y que cada celda de código parsea (`ast.parse`); la ejecución real (yfinance + Spark + `dbutils.notebook.run`) requiere un workspace de Databricks real, no verificable desde este repo.
- Es el primer uso de `dbutils.notebook.run`/`.exit` y de escritura a Delta en todo el repo — no había un patrón previo que seguir para ninguno de los dos.

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
3. **`src/agents/base_agent.py` tenía un import roto**: hacía `sys.path.insert(0, '/Workspace/Users/matiasadell@hotmail.com')` y `from agentic_ai_platform.src.utils.config import Settings` — un prefijo de paquete (`agentic_ai_platform.`) que no usa ningún otro archivo del repo, más una ruta hardcodeada a un workspace de Databricks específico. Corregido a `from src.utils.config import Settings`, igual que el resto del código.
   **Corrección de la severidad que le había asignado antes:** dije que esto "rompía el import de toda la capa Workers" porque asumí (sin verificar) que los 7 workers extendían `BaseAgent`. **No es así** — ninguno lo extiende, y nada en `src/` importa `BaseAgent` en absoluto (verificado con grep). `BaseAgent` está completamente desconectada del pipeline que funciona; el fix es correcto y vale la pena tenerlo andando para quien lo use a futuro, pero no estaba bloqueando nada activo. Ver la sección "Qué LLM se usa realmente" más abajo para el detalle completo de esta desconexión.
4. **`src/agents/tools/` y `src/workers/` no tenían `__init__.py`** (a diferencia de todos sus paquetes hermanos). No rompía imports corriendo desde el repo (namespace packages de Python 3), pero `pyproject.toml` usaba `[tool.setuptools.packages.find]` (no `find_namespace`), que solo descubre paquetes con `__init__.py` — un `pip install .` real probablemente excluía `uc_functions.py` y `src/workers/fundamental.py` del paquete instalado. Se agregaron ambos `__init__.py` (siguen siendo correctos aunque `pyproject.toml` ya no exista — ver más abajo).
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

Cleanup 2026-08-11 (esta sesión): eliminado `agentic-ai-platform.zip` + `unzip.py` (archivo comprimido del propio repo, commiteado por error) y `manifest.mf` (metadata de herramienta externa, no contenido real); documentación raíz consolidada en `docs/`; `8-multiagent.py` movido de la raíz a `notebooks/` y los tres archivos de `notebooks/` (`8-multiagent`, `example_agent_usage`, `setup_uc_functions`) convertidos de formato "Databricks notebook source" plano (`.py`/`.sql`) a `.ipynb` real; auditoría estática de imports sobre los 32 archivos de `src/` y fixes aplicados — ver "✅ Corregido el 2026-08-11" arriba (import roto en `base_agent.py`, dos supervisors `_langgraph` reescritos, `__init__.py` faltantes, docstrings y exports de schemas corregidos); `pyproject.toml` reemplazado por `requirements.txt` — este repo nunca fue pensado como paquete instalable, se ejecuta como notebooks/jobs de Databricks, así que el `[build-system]`/`packages.find` de `pyproject.toml` no cumplía ninguna función real; `requirements.txt` se armó escaneando los imports reales de `src/` y `notebooks/` en vez de copiar la lista de ~40 dependencias original (muchas nunca importadas: FastAPI, LiteLLM, MCP, Neo4j, SQLAlchemy, psycopg2, ragas, sec-api, yfinance, databricks-vectorsearch, y los extras de airflow/monitoring). De paso se detectaron 5 paquetes que el código sí usa pero que `pyproject.toml` nunca había listado: `databricks-langchain`, `langchain-experimental`, `langchain-tavily`, `langgraph-supervisor`, `wikipedia`. (Se creó también un `requirements-dev.txt` con pytest/black/ruff/mypy/jupyter, luego eliminado a pedido — no hace falta por ahora.)

Nuevo 2026-08-11 (misma sesión, arranque del lado de data engineering): pipeline de ingesta batch de yfinance — `config/data_ingest/{daily_batch_config,catalog_config}.json` + `notebooks/data/data_ingest/{orchestrator,worker}.ipynb`. Ver la sección "Data Engineering" arriba para el detalle. `yfinance` vuelve a `requirements.txt` (se había sacado en el paso anterior por no usarse).

**Nota:** en esta misma sesión el usuario borró `.gitignore` y `LICENSE` intencionalmente (no accidental). Como `.gitignore` ya no existe, no hay red de seguridad contra trackear en git cosas como `.env`, `venv/`, `.pytest_cache/`, logs, etc. — el riesgo de `__pycache__/` específicamente ya está cubierto sin necesitar `.gitignore` porque `src/__init__.py` setea `sys.dont_write_bytecode = True`, así que Python directamente no genera esos archivos al importar `src.*` (se descartó la alternativa de la variable de entorno `PYTHONDONTWRITEBYTECODE` porque la configuración por env var de este proyecto va a migrar a Databricks Secrets, que no es el lugar para un flag de intérprete). `LICENSE` (MIT) sigue sin restaurar — el repo es privado así que no es urgente, pero si se vuelve público o se suma gente, su ausencia implica "todos los derechos reservados" por defecto, y ahora que `pyproject.toml` tampoco existe no queda ninguna mención del license en el repo.

---

## 🚀 Próximos pasos sugeridos

1. **Decidir cuál supervisor es el canónico por dominio** ahora que los tres `_langgraph.py` importan correctamente: quedarse con la versión manual (`macro_supervisor.py`, `news_supervisor.py`, `fundamental_supervisor_v2.py`) o migrar a la declarativa (`*_langgraph.py`) y borrar la otra. Tenerlas todas vivas y sin uso es la causa original de la confusión.
2. **Decidir el mecanismo de LLM real**: ¿migrar los 7 workers + Fundamental a `BaseAgent`/AI Gateway (governance centralizado, MLflow logging, un solo lugar para cambiar de modelo), o aceptar/documentar formalmente que Llama 3.3 directo (Macro/News) y OpenAI directo (Fundamental) son el diseño real y borrar/actualizar `BaseAgent` y `docs/AI_GATEWAY_CONFIG.md` para que dejen de describir algo que no se usa?
3. **Unificar** `src/workers/` dentro de `src/agents/workers/` (o viceversa) para tener una sola jerarquía.
4. **Rotar y remover** las API keys hardcodeadas en `notebooks/8-multiagent.ipynb` y `.env.example`.
5. **Actualizar o borrar** `config/mcp_tools.yaml` (referencia código que ya no existe).
6. Recién después de eso: Strategic Orchestrator, RAG, evaluación, tests.

---

**Mantenido por:** Matias Adell
