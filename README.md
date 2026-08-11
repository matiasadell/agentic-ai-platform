# 🧠 FinSight AI — Plataforma de Inteligencia Financiera Autónoma

> Sistema multi-agente jerárquico de 3 niveles para análisis financiero automatizado con **Unity Catalog Functions** como tools nativos, **Databricks AI Gateway** para governance, RAG strategies especializadas, knowledge graph, y observabilidad completa.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)](https://langchain-ai.github.io/langgraph/)
[![Databricks](https://img.shields.io/badge/Databricks-Unity_Catalog-orange.svg)](https://www.databricks.com/)
[![AI Gateway](https://img.shields.io/badge/AI_Gateway-Databricks-purple.svg)](https://docs.databricks.com/en/generative-ai/agent-framework/index.html)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-red.svg)](https://neo4j.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 ¿Qué es FinSight AI?

**No es un chatbot financiero. Es una sala de análisis automatizada.**

Dado un objetivo de investigación como *"Analizar el riesgo de inversión en el sector energético argentino considerando el contexto macro regional"*, el sistema:

1. **Planifica autónomamente** la investigación completa
2. **Ejecuta** con agentes especializados en paralelo usando **UC Functions como tools nativos**
3. **Gobierna** con **Databricks AI Gateway** (rate limits, usage tracking, policies)
4. **Valida** la calidad de información entre fuentes
5. **Detecta** contradicciones automáticamente
6. **Genera** un reporte institucional con citación completa y niveles de confianza

---

## 🏗️ Arquitectura Jerárquica de 3 Niveles

```
┌─────────────────────────────────────────────────────────┐
│         Strategic Orchestrator (Nivel 1)                │
│   Plan-Execute-Replan | Human-in-the-loop              │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼────────┐ ┌─────▼──────────┐ ┌──────▼─────────┐
│  Macro & Market│ │  Fundamental   │ │ News & Sentiment│
│   Supervisor   │ │   Supervisor   │ │   Supervisor    │
│   (Nivel 2)    │ │   (Nivel 2)    │ │   (Nivel 2)     │
└───────┬────────┘ └────────┬───────┘ └────────┬────────┘
        │                   │                   │
  ┌─────┴─────┐      ┌──────┴──────┐     ┌─────┴──────┐
  │  Workers  │      │   Workers   │     │  Workers   │
  │ (Nivel 3) │      │  (Nivel 3)  │     │ (Nivel 3)  │
  │           │      │             │     │            │
  │ UC Tools  │      │  UC Tools   │     │ UC Tools   │
  └─────┬─────┘      └──────┬──────┘     └─────┬──────┘
        └───────────┬────────┴────────┬─────────┘
                    │                 │
       ┌────────────▼─────────┐   ┌───▼──────────────────┐
       │ Unity Catalog        │   │  AI Gateway          │
       │ Python Functions     │   │  • Rate Limits       │
       │ • get_gdp_data       │   │  • Usage Tracking    │
       │ • get_inflation_data │   │  • Policies          │
       │ • get_unemployment   │   │  • Inference Table   │
       │ • get_interest_rate  │   └──────────────────────┘
       │ • get_financial_news │
       └──────────────────────┘
```

---

## 🚀 Innovaciones Clave

### 🔌 Unity Catalog Functions como Tools Nativos

**Tools gobernados en Unity Catalog:**

```
┌─────────────────────────────────────────┐
│   Unity Catalog Functions (5)           │
├─────────────────────────────────────────┤
│ • get_gdp_data (World Bank API)         │
│ • get_inflation_data (World Bank API)   │
│ • get_unemployment_data (World Bank API)│
│ • get_interest_rate (USA, placeholder)  │
│ • get_financial_news (NewsAPI)          │
└─────────────────────────────────────────┘
        ↓ Expuestas como LangChain Tools
┌─────────────────────────────────────────┐
│    Agentes LLM invocan via @tool        │
│    El LLM decide cuándo llamarlas       │
└─────────────────────────────────────────┘
```

**Beneficios:**
- ✅ **Zero infra adicional** - Sin Databricks Apps DBU consumption
- ✅ **Governance nativo** - UC permissions, audit logs
- ✅ **Hot reload** - Actualizar funciones sin redeployar workers
- ✅ **Central discovery** - `SHOW FUNCTIONS IN main.finsight_ai`
- ✅ **Multi-agent reuse** - Mismas functions para todos los workers
- ✅ **Tool calling nativo** - LLM invoca tools automáticamente

### 🛡️ Databricks AI Gateway

**Governance y control centralizado de LLM endpoints:**

```yaml
# Endpoint único para todos los agentes
Endpoint: ai-gateway:/main.finsight_ai.finsight-chat
Model: databricks-meta-llama-3-1-405b-instruct

Governance:
  - Rate Limits: 200 QPM, 100K TPM
  - Usage Tracking: system.ai_gateway.usage
  - Inference Table: Request/response logging
  - Policies: Input/output guardrails
```

**Funcionalidades:**
- 🎯 **Single Endpoint** - Todos los workers usan el mismo endpoint
- 📊 **Usage Tracking** - Costos y tokens por agent/user
- 🚦 **Rate Limiting** - Protección contra overuse
- 📝 **Inference Table** - Log completo de requests/responses
- 🛡️ **Guardrails** - Policies para input/output filtering
- 🔍 **Observability** - Lineage y debugging integrados

---

## 🔧 Stack Tecnológico

### Backend & Orchestration
- **LangGraph** — Orquestación multi-agente con checkpoints
- **FastAPI** — API async con endpoints RESTful
- **Databricks Runtime** — Serverless compute (Python, SQL)
- **Unity Catalog** — Functions como tools gobernados

### LLM & AI
- **Meta Llama 3.1 405B** — Modelo foundation principal
- **Databricks AI Gateway** — Governance, rate limits, usage tracking
- **LangChain Tool Calling** — UC Functions como @tool nativos

### Storage & Databases
- **Databricks Vector Search** — Embeddings y documentos
- **Neo4j** — Knowledge graph financiero
- **Redis** — Cache de API calls y semantic caching
- **Delta Tables** — Historial de investigaciones
- **PostgreSQL** — LiteLLM usage tracking

### Tools & APIs (via UC Functions)
- **World Bank API** — GDP, inflation, unemployment (pública)
- **NewsAPI** — Financial news search
- **Databricks Secrets** — Secure API key management
- **Unity Catalog** — Function registry y governance
- **LangChain @tool** — Tool calling nativo

### Observability
- **AI Gateway Inference Table** — Request/response logging
- **Unity Catalog Audit Logs** — Function invocation tracking
- **MLflow** — Experiment tracking
- **Databricks Lineage** — Data + UC Functions lineage

---

## 📋 Instalación Rápida

### Pre-requisitos
- Python 3.10+
- Docker (para Neo4j, Redis, PostgreSQL)
- Databricks Workspace con Vector Search
- API Keys: OpenAI, Anthropic, Alpha Vantage, Tavily, LangSmith

### 1. Clonar y Configurar
```bash
git clone https://github.com/matiasadell/agentic-ai-platform.git
cd agentic-ai-platform

# Configurar environment
cp .env.example .env
# Editar .env con tus API keys
```

### 2. Instalar Dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 3. Iniciar Infraestructura
```bash
# Neo4j + Redis + PostgreSQL con Docker
docker-compose up -d

# Inicializar Neo4j schema
python scripts/init_neo4j.py
```

### 4. Iniciar Servicios
```bash
# Opción A: Todo en uno
./scripts/start_all.sh

# Opción B: Servicios individuales
./scripts/start_litellm.sh       # LiteLLM Proxy
./scripts/start_mcp_servers.sh   # MCP Servers
uvicorn src.api.main:app --reload  # FastAPI
```

### 5. Verificar
- **LiteLLM Admin:** http://localhost:4000/ui
- **API Docs:** http://localhost:8000/docs
- **Health Check:** `curl http://localhost:8000/health`

---

## 💡 Uso Rápido

### Crear una Investigación
```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/research",
    json={
        "objective": "Analizar sector energético argentino",
        "depth": "comprehensive",
        "human_approval_required": True
    }
)

research_id = response.json()["research_id"]
```

### Monitorear Progreso
```python
status = httpx.get(f"http://localhost:8000/api/v1/research/{research_id}")
print(status.json())
```

### Obtener Reporte
```python
report = httpx.get(f"http://localhost:8000/api/v1/research/{research_id}/report")
print(report.json())
```

---

## 💰 Optimización de Costos con LiteLLM

### Budget Protection
```yaml
budget:
  max_monthly_budget: 10000  # USD
  downgrade_threshold: 0.9
  emergency_model: "gpt-4o-mini"
```

### Semantic Caching
```python
# Primera llamada: $0.03
response1 = completion(messages=["Analyze AAPL stock"])

# Segunda llamada similar: $0.00 (cache hit)
response2 = completion(messages=["Analyze Apple stock"])
```

### Model Routing
```python
# Tarea compleja → GPT-4o ($$$)
synthesis_task = {"task": "synthesis", ...}

# Tarea simple → GPT-4o-mini ($)
extraction_task = {"task": "extraction", ...}
```

**Ahorro típico:** 40-60% en costos de LLM

---

## 📊 Monitoreo en Tiempo Real

### LiteLLM Admin UI
Accede a `http://localhost:4000/ui` para ver:
- 💵 Costos en tiempo real
- ⚡ Latencias por modelo
- 📈 Request rates
- 🎯 Cache hit rates
- ⚠️ Errores y fallbacks

### LangSmith Tracing
Cada llamada LLM es traced con:
- Input/output completos
- Latencia y tokens
- Metadata del agente
- Chain of thought

---

## 🧪 Testing

```bash
# Tests unitarios
pytest tests/unit

# Tests de integración
pytest tests/integration

# Tests de MCP tools
pytest tests/mcp

# Tests de LiteLLM routing
pytest tests/litellm
```

---

## 📁 Estructura del Proyecto

```
agentic-ai-platform/
├── src/
│   ├── agents/              # Orchestrator, Supervisors, Workers
│   │   ├── base_agent.py    # BaseAgent con AI Gateway
│   │   └── workers/         # MacroDataWorker, MarketSentimentWorker
│   ├── tools/
│   │   └── uc_functions.py  # UC Functions como LangChain @tool
│   ├── rag/                 # RAG strategies
│   ├── graph/               # Neo4j integration
│   ├── api/                 # FastAPI routes
│   ├── evaluation/          # RAGAS evaluation
│   ├── guardrails/          # Input/output validation
│   └── utils/               # Config, logging, cache
├── notebooks/
│   ├── setup_uc_functions.sql  # CREATE FUNCTION statements
│   └── test_workers.py         # Worker testing notebook
├── config/
│   ├── agent_configs.yaml   # Agent configuration
│   └── rag_configs.yaml     # RAG strategies
├── docs/
│   ├── architecture.md      # Technical architecture
│   ├── AI_GATEWAY_CONFIG.md # AI Gateway setup
│   ├── SECURITY_SETUP.md    # Secrets management
│   └── PROJECT_STATUS.md    # Roadmap
└── tests/                   # Comprehensive tests
```

---

## 📚 Documentación

- **README.md** - Este archivo
- **[docs/architecture.md](docs/architecture.md)** - Arquitectura técnica detallada
- **[docs/MCP_LITELLM.md](docs/MCP_LITELLM.md)** - Guía de MCP y LiteLLM
- **[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** - Estado y roadmap
- **[QUICKSTART.md](QUICKSTART.md)** - Guía de inicio rápido

---

## 🎓 Lo que Demuestra Este Proyecto

✅ **Arquitectura multi-agente jerárquica real** (no solo teórico)  
✅ **Unity Catalog Functions como tools nativos** (zero infra adicional)  
✅ **Databricks AI Gateway** (governance + rate limits + observability)  
✅ **LangChain tool calling** (LLM decide cuándo invocar UC Functions)  
✅ **Secrets management** (Databricks Secrets para API keys)  
✅ **Decisiones de diseño justificadas** (por qué UC Functions > MCP)  
✅ **Production-ready** (hot reload, audit logs, lineage, central discovery)  

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guidelines.

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

---

## 📧 Contacto

**Matias Adell**  
Email: matiasadell@hotmail.com  
LinkedIn: [linkedin.com/in/matiasadell](https://linkedin.com/in/matiasadell)  
GitHub: [@matiasadell](https://github.com/matiasadell)

---

**⭐ Si este proyecto te resulta útil, considera darle una estrella en GitHub ⭐**


## 🏢 Fundamental Analysis Layer

### Schemas (`src/schemas/fundamental.py`)
- **FinancialStatementResponse** - Balance sheet, income statement, cash flow
- **KeyRatiosResponse** - P/E, ROE, ROA, margins, liquidity, efficiency ratios
- **EarningsResponse** - EPS surprise, revenue beats, guidance, analyst ratings
- **ValuationResponse** - DCF, comparables, intrinsic value, upside/downside

### Workers (`src/workers/fundamental.py`)
- **FinancialStatementWorker** - Analyzes financial statements (balance, income, cash flow)
- **KeyRatiosWorker** - Calculates valuation, profitability, liquidity ratios
- **EarningsWorker** - Analyzes earnings reports, EPS/revenue surprises, guidance
- **ValuationWorker** - Performs DCF and comparables valuation analysis

### Supervisor (`src/agents/supervisors/fundamental_supervisor_langgraph.py`)
- **FundamentalSupervisor** (LangGraph StateGraph)
  - 6 nodes: router + 4 workers + synthesis
  - Parallel execution (automatic via conditional_edges)
  - Ticker-aware routing
  - Metric extraction (revenue, P/E, EPS, fair value)
  - Graceful degradation



## ✅ LangGraph Migration Complete

All supervisors now use **LangGraph** (declarative StateGraph):

- ✅ **MacroSupervisor** (287 lines) - `macro_supervisor_langgraph.py`
- ✅ **NewsSupervisor** (326 lines) - `news_supervisor_langgraph.py`
- ✅ **FundamentalSupervisor** (337 lines) - `fundamental_supervisor_langgraph.py`

**Benefits:**
- 70% less code vs manual orchestration
- Automatic parallel execution
- Built-in state management (TypedDict + Annotated)
- Mermaid visualization support
- Industry-standard architecture
- Production-ready

**Total:** 12 workers, 3 supervisors, ALL LangGraph! 🚀
