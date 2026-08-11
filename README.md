# 🧠 FinSight AI — Plataforma de Inteligencia Financiera Autónoma

> Sistema multi-agente jerárquico para análisis financiero automatizado, nativo de Databricks: **Unity Catalog Functions** como tools, **Databricks AI Gateway** para el routing de LLM, **LangGraph** para orquestación, **MLflow** para observabilidad.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)](https://langchain-ai.github.io/langgraph/)
[![Databricks](https://img.shields.io/badge/Databricks-Unity_Catalog-orange.svg)](https://www.databricks.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🚧 **Proyecto en desarrollo activo.** No todo lo descrito abajo está terminado — algunos supervisors están rotos y hay módulos duplicados/huérfanos. El estado real y verificado del código vive en **[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)**; léelo antes de asumir que algo funciona.

---

## 🎯 ¿Qué es FinSight AI?

Dado un objetivo de investigación como *"Analizar el riesgo de inversión en el sector energético argentino considerando el contexto macro regional"*, la idea es que el sistema:

1. Descomponga la investigación en sub-tareas por dominio (macro, fundamental, news/sentiment)
2. Ejecute agentes especializados que usan **Unity Catalog Functions** como tools nativos
3. Coordine todo vía **Databricks AI Gateway** (rate limits, usage tracking, governance)
4. Sintetice un reporte con citación y niveles de confianza

Hoy, los tres dominios (Macro, News, Fundamental) tienen supervisors funcionales que coordinan sus workers/agents individualmente. La capa de orquestación de nivel superior (Strategic Orchestrator), síntesis de reporte, RAG y knowledge graph todavía no están implementados — ver [PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

---

## 🏗️ Arquitectura

Diseño completo (target) en **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**. Resumen de los 2 niveles que sí existen hoy:

```
        Macro Supervisor        Fundamental Supervisor      News Supervisor
        (macro_supervisor.py)   (fundamental_supervisor_v2.py) (news_supervisor.py)
              │                          │                          │
     ┌────────┼────────┐                 │            ┌─────────────┼─────────────┐
     │        │        │          4 ReAct Agents       │             │             │
 MacroData Regional Indicator    (fundamental_agents.py) MarketSent EventDetect  General/Sector
  Worker   Context  Analysis                              Worker     Worker         News Workers
```

Cada worker/agent usa Unity Catalog Functions (`src/agents/tools/uc_functions.py`, definidas en `notebooks/setup_uc_functions.ipynb`) como tools, invocadas vía Databricks AI Gateway.

---

## 🔧 Stack Tecnológico

- **LangGraph** — orquestación de agentes/supervisors (StateGraph)
- **Databricks AI Gateway** — routing de LLM, rate limiting, usage tracking
- **Unity Catalog Functions** — tools gobernados, expuestos como `@tool` de LangChain
- **MLflow** (nativo de Databricks) — tracing y métricas
- **Pydantic** — configuración (`src/utils/config.py`) y schemas de respuesta (`src/schemas/`)

Fuentes de datos externas: World Bank API, FRED, Alpha Vantage, Financial Modeling Prep, NewsAPI, SEC EDGAR, Tavily.

No hay FastAPI, Docker, Neo4j, Redis ni tests automatizados en el repo actualmente — versiones anteriores de esta documentación los mencionaban como parte del stack, pero eso corresponde a un diseño anterior descartado. Ver [docs/DATABRICKS_NATIVE_ARCHITECTURE.md](docs/DATABRICKS_NATIVE_ARCHITECTURE.md) para el porqué.

---

## 📋 Instalación Rápida

Guía completa en **[docs/QUICKSTART.md](docs/QUICKSTART.md)**. Resumen:

```bash
git clone https://github.com/matiasadell/agentic-ai-platform.git
cd agentic-ai-platform
cp .env.example .env   # completar con tus API keys — ver docs/SECURITY_SETUP.md

python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Requiere un workspace de Databricks con Unity Catalog y un AI Gateway endpoint configurado — `src/agents/base_agent.py` llama directamente a `databricks.sdk.WorkspaceClient`, no corre standalone fuera de Databricks.

---

## 📁 Estructura del Proyecto

```
agentic-ai-platform/
├── src/
│   ├── agents/
│   │   ├── base_agent.py        # Clase base: AI Gateway + MLflow + tool loop
│   │   ├── fundamental_agents.py # 4 ReAct agents (dominio Fundamental)
│   │   ├── workers/              # 7 workers (dominios Macro y News)
│   │   ├── supervisors/          # macro_supervisor, news_supervisor, fundamental_supervisor_v2
│   │   └── tools/uc_functions.py # Unity Catalog Functions como @tool
│   ├── workers/fundamental.py    # Variante alternativa del dominio Fundamental (no usada activamente)
│   ├── schemas/                  # Modelos Pydantic de respuesta por dominio
│   └── utils/                    # config, logging, cache
├── notebooks/                     # Notebooks reales (.ipynb)
│   ├── setup_uc_functions.ipynb  # CREATE FUNCTION de las 9 UC Functions
│   ├── example_agent_usage.ipynb
│   └── 8-multiagent.ipynb        # Notebook de referencia (patrón LangGraph)
├── config/
│   ├── agent_configs.yaml
│   └── mcp_tools.yaml            # ⚠️ desactualizado, ver PROJECT_STATUS.md
└── docs/                         # Toda la documentación vive acá
```

Ver [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) para qué archivos están rotos o duplicados.

---

## 📚 Documentación

Toda la documentación está en [`docs/`](docs/):

- **[PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** — estado real, verificado contra el código: qué funciona, qué está roto, próximos pasos
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — diseño completo del sistema (target) + historial del cambio de paradigma Workers → Agents
- **[QUICKSTART.md](docs/QUICKSTART.md)** — guía de inicio
- **[AI_GATEWAY_CONFIG.md](docs/AI_GATEWAY_CONFIG.md)** — configuración del AI Gateway
- **[SECURITY_SETUP.md](docs/SECURITY_SETUP.md)** — manejo de secretos (Databricks Secrets)
- **[WORKER_VERSIONS_GUIDE.md](docs/WORKER_VERSIONS_GUIDE.md)** — qué patrón usa cada dominio (Workers vs Agents)
- **[DATABRICKS_NATIVE_ARCHITECTURE.md](docs/DATABRICKS_NATIVE_ARCHITECTURE.md)** — por qué se descartó el diseño híbrido (LiteLLM/FastAPI/MCP custom) a favor de servicios nativos de Databricks

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas — leé [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) primero para saber en qué estado está cada parte antes de tocarla.

## 📄 Licencia

MIT License — ver [LICENSE](LICENSE).

## 📧 Contacto

**Matias Adell**
GitHub: [@matiasadell](https://github.com/matiasadell)

---

**⭐ Si este proyecto te resulta útil, considera darle una estrella en GitHub ⭐**
