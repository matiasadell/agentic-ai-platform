# 🚀 Quickstart Guide - FinSight AI

**Tiempo estimado:** 15-20 minutos

---

## Paso 1: Verificar Requisitos

### Python 3.10+
```bash
python3 --version
# Debe ser >= 3.10
```

### Git
```bash
git --version
```

---

## Paso 2: Obtener API Keys

Antes de comenzar, obtén estas API keys (solo las marcadas con ✓ son necesarias para empezar):

| Servicio | Requerido | Cómo obtener |
|----------|-----------|--------------|
| ✓ OpenAI | MVP | https://platform.openai.com/api-keys |
| ✓ Anthropic | MVP | https://console.anthropic.com/ |
| ✓ LangSmith | MVP | https://smith.langchain.com/ |
| ✓ Alpha Vantage | MVP | https://www.alphavantage.co/support/#api-key |
| ✓ Tavily | MVP | https://tavily.com/ |
| ○ SEC API | Opcional | https://sec-api.io/ |
| ○ NewsAPI | Opcional | https://newsapi.org/ |

---

## Paso 3: Configuración del Proyecto

### 3.1 Navegar al proyecto (ya estás aquí)
```bash
cd /Workspace/Users/matiasadell@hotmail.com/agentic-ai-platform
```

### 3.2 Configurar API Keys

#### 🔐 **RECOMENDADO: Databricks Secrets (Producción)**

Si estás en Databricks, **usa Databricks Secrets** para máxima seguridad:

```python
# En tu notebook
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Agregar secrets (una sola vez)
w.secrets.put_secret(scope="finsight", key="fred-api-key", string_value="YOUR_KEY")
w.secrets.put_secret(scope="finsight", key="news-api-key", string_value="YOUR_KEY")
w.secrets.put_secret(scope="finsight", key="alpha-vantage-api-key", string_value="YOUR_KEY")

# Luego, leer secrets en tu código
import os
os.environ['FRED_API_KEY'] = dbutils.secrets.get(scope="finsight", key="fred-api-key")
os.environ['NEWS_API_KEY'] = dbutils.secrets.get(scope="finsight", key="news-api-key")
```

**Ver documentación completa:** [SECURITY_SETUP.md](./SECURITY_SETUP.md)

#### 📄 Alternativa: Variables de entorno (.env) - Solo para desarrollo local

```bash
cp .env.example .env
```

Edita `.env` con tus API keys:
```bash
# Obligatorias para MVP
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LANGCHAIN_API_KEY=ls__...
ALPHA_VANTAGE_API_KEY=...
TAVILY_API_KEY=tvly-...

# Databricks (si tienes workspace configurado)
DATABRICKS_HOST=https://...
DATABRICKS_TOKEN=dapi...

# Neo4j (local o cloud)
NEO4J_PASSWORD=tu-password
```

⚠️ **NUNCA comitees el archivo .env a Git**

---

## Paso 4: Instalación (En tu máquina local)

### Opción A: Script automático (recomendado)
```bash
./scripts/setup.sh
```

### Opción B: Manual
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -e ".[dev]"
```

---

## Paso 5: Inicializar Bases de Datos

### Neo4j

**Opción A: Docker (recomendado para desarrollo)**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:latest
```

**Opción B: Instalación local**
Descargar desde: https://neo4j.com/download/

**Inicializar schema:**
```bash
python scripts/init_neo4j.py
```

### Redis

**Opción A: Docker**
```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

**Opción B: Instalación local**
- Mac: `brew install redis`
- Linux: `sudo apt-get install redis-server`

### Vector Search

**Databricks Vector Search** (requiere workspace configurado)
```bash
python scripts/init_vector_search.py
```

---

## Paso 6: Verificar Instalación

### 6.1 Tests básicos
```bash
pytest tests/ -v
```

### 6.2 Verificar imports
```python
from src.utils.config import settings
from src.utils.logging import setup_logging, logger

setup_logging()
logger.info("FinSight AI configurado correctamente!")
```

---

## Paso 7: Primera Ejecución (Conceptual)

**NOTA:** El MVP aún no está implementado. Estos serán los pasos cuando esté listo:

### 7.1 Iniciar API
```bash
uvicorn src.api.main:app --reload
```

### 7.2 Crear una investigación
```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Analizar sector energético argentino",
    "depth": "basic",
    "human_approval_required": false
  }'
```

### 7.3 Consultar estado
```bash
curl "http://localhost:8000/api/v1/research/{research_id}"
```

---

## 🔧 Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
# Asegúrate de estar en el entorno virtual
source venv/bin/activate

# Reinstalar el proyecto
pip install -e .
```

### Error: "Neo4j connection refused"
```bash
# Verificar que Neo4j esté corriendo
docker ps | grep neo4j

# O si es local:
neo4j status
```

### Error: "Redis connection refused"
```bash
# Verificar que Redis esté corriendo
docker ps | grep redis

# O si es local:
redis-cli ping
# Debe responder: PONG
```

### Error: "API key not found"
```bash
# Verificar que .env esté en el directorio raíz
ls -la .env

# Verificar que las variables estén cargadas
python -c "from src.utils.config import settings; print(settings.openai_api_key[:10])"
```

---

## 📖 Siguiente Pasos

1. **Leer la documentación:**
   - `README.md` - Visión general
   - `docs/architecture.md` - Arquitectura detallada
   - `docs/PROJECT_STATUS.md` - Roadmap y próximos pasos

2. **Explorar el código base:**
   - `src/utils/` - Utilidades configuradas
   - `config/` - Configuración de agentes y RAG
   - `tests/` - Estructura de tests

3. **Empezar a desarrollar:**
   - Ver `docs/PROJECT_STATUS.md` sección "Próximos Pasos"
   - Comenzar con Fase 1: Base Classes & Tools

---

## 🆘 Ayuda

### Documentación
- README.md
- docs/architecture.md
- docs/information.md
- docs/PROJECT_STATUS.md

### Contacto
- Email: matiasadell@hotmail.com
- GitHub: @matiasadell

---

**¡Listo! El proyecto está configurado y listo para desarrollo.** 🎉
