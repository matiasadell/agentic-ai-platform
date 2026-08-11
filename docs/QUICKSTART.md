# 🚀 Quickstart — FinSight AI

> Movido desde `QUICKSTART.md` (raíz) y actualizado el 2026-08-11: la versión anterior asumía Docker, Neo4j, Redis, `scripts/setup.sh`, `src/api/main.py` (FastAPI) y `tests/` — nada de eso existe en el repo. Este proyecto corre **nativamente en Databricks**; no hay servicios locales que levantar.

**Tiempo estimado:** 10-15 minutos.

---

## Paso 1: Requisitos

- Python 3.10+ (`python3 --version`)
- Un workspace de Databricks con:
  - Unity Catalog habilitado
  - Un AI Gateway endpoint configurado (ver [AI_GATEWAY_CONFIG.md](./AI_GATEWAY_CONFIG.md))
  - Un SQL Warehouse
- Git

## Paso 2: API Keys necesarias

| Servicio | Requerido | Dónde conseguirla |
|----------|-----------|--------------------|
| Databricks host + token | Sí | Tu workspace de Databricks |
| Alpha Vantage | Sí | https://www.alphavantage.co/support/#api-key |
| Financial Modeling Prep | Sí | https://site.financialmodelingprep.com/developer/docs |
| NewsAPI | Sí | https://newsapi.org/register |
| Tavily | Sí | https://tavily.com/ |
| SEC EDGAR | No (no requiere key, solo header `User-Agent`) | — |
| OpenAI / Anthropic | Opcional (el routing de LLM real pasa por AI Gateway) | — |

Estas son exactamente las variables que pide `src/utils/config.py` (`Settings`) — si falta alguna obligatoria, el proyecto no arranca.

## Paso 3: Clonar y configurar

```bash
git clone https://github.com/matiasadell/agentic-ai-platform.git
cd agentic-ai-platform
cp .env.example .env
```

Editá `.env` con tus keys reales.

⚠️ **Nunca commitees `.env`.** Este repo no tiene `.gitignore` (se eliminó intencionalmente), así que `.env` **no está excluido de git** — prestá atención antes de hacer `git add`. Para producción, usá Databricks Secrets en vez de `.env` — ver [SECURITY_SETUP.md](./SECURITY_SETUP.md).

> ⚠️ Nota de seguridad: al momento de este documento, `.env.example` en el repo contiene una API key real de Financial Modeling Prep hardcodeada (no un placeholder), y `notebooks/8-multiagent.ipynb` tiene una key de Tavily hardcodeada. Ambas deberían rotarse — ver [PROJECT_STATUS.md](./PROJECT_STATUS.md#5-secretos-hardcodeados-en-el-repo-seguridad-no-solo-documentación).

## Paso 4: Instalar dependencias

Este repo no es un paquete Python instalable (no hay `pyproject.toml`) — las dependencias están en `requirements.txt`:

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

No hay `requirements-dev.txt` por ahora (herramientas de testing/linting como pytest, black, ruff — no hace falta instalarlas para correr el código, solo si en algún momento se agrega testing/linting al proyecto).

(No hay `scripts/setup.sh` en el repo — la instalación es directamente con `pip`. `requirements.txt` está armado a partir de un escaneo de los imports reales en `src/` y `notebooks/`, no es una lista aspiracional — ver la cabecera del archivo y [PROJECT_STATUS.md](./PROJECT_STATUS.md) para el detalle de qué se dejó afuera de la vieja `pyproject.toml`.)

`pyspark` no está en `requirements.txt` a propósito aunque el código lo importa (`uc_functions.py`, `macro_data_worker.py`) — los clusters de Databricks ya lo proveen vía el runtime; instalarlo localmente puede generar conflictos de versión con el del cluster.

### `__pycache__/` no se escribe

Este repo no tiene `.gitignore`, así que la única protección contra `__pycache__/` es que directamente no se genera: `src/__init__.py` setea `sys.dont_write_bytecode = True` apenas se importa cualquier cosa de `src.*`, sin depender de una variable de entorno que haya que configurar en cada lugar donde esto corre (local, notebook de Databricks, cluster/job). Única excepción: el propio `src/__init__.py` se cachea una vez, antes de que su código llegue a ejecutarse (limitación del mecanismo, no algo a arreglar). Otros artefactos (`.pytest_cache/`, `venv/`, logs, `.env`) no tienen ninguna protección — no hay `.gitignore` que los excluya, así que hay que tener cuidado al hacer `git add`.

## Paso 5: Crear las Unity Catalog Functions

Las tools que usan los agentes viven como funciones de Unity Catalog, no como servidores custom. Corré el SQL de:

```
notebooks/setup_uc_functions.ipynb
```

en tu workspace de Databricks (crea las 9 Unity Catalog functions: `get_gdp_data`, `get_inflation_data`, `get_unemployment_data`, `get_interest_rate`, `get_financial_news`, `get_regional_news`, `get_stock_prices`, `get_technical_indicators`, `detect_corporate_events`).

## Paso 6: Verificar

```python
from src.utils.config import settings
from src.utils.logging import setup_logging, logger

setup_logging()
logger.info("Config cargada correctamente")
```

Y probar un supervisor (los que realmente funcionan hoy — ver [PROJECT_STATUS.md](./PROJECT_STATUS.md) para el estado completo):

```python
from src.agents.supervisors.macro_supervisor import MacroSupervisor
# o: from src.agents.supervisors.news_supervisor import NewsSupervisor
# o: from src.agents.supervisors.fundamental_supervisor_v2 import get_fundamental_supervisor
```

`src/agents/base_agent.py` asume que corre dentro de un notebook/job de Databricks (usa `databricks.sdk.WorkspaceClient` para llamar al AI Gateway) — importa bien en cualquier entorno, pero ejecutar un worker de verdad requiere credenciales de un workspace de Databricks.

## 🔧 Problemas comunes

**`ModuleNotFoundError`**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**`pydantic.ValidationError` al importar `settings`**
Falta una variable obligatoria en `.env` (ver Paso 2). El mensaje de error de Pydantic te dice cuál.

**Error llamando al AI Gateway**
Verificá que el endpoint exista y que tengas permisos:
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
w.serving_endpoints.query(name="finsight-chat", messages=[...])
```
Ver [AI_GATEWAY_CONFIG.md](./AI_GATEWAY_CONFIG.md).

---

## 📖 Siguiente

- [PROJECT_STATUS.md](./PROJECT_STATUS.md) — qué funciona hoy, qué está roto, próximos pasos
- [ARCHITECTURE.md](./ARCHITECTURE.md) — diseño del sistema
- [SECURITY_SETUP.md](./SECURITY_SETUP.md) — manejo de secretos
