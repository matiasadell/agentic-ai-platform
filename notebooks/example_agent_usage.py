# Databricks notebook source
# DBTITLE 1,📚 FinSight AI - Agent Usage Examples
# MAGIC %md
# MAGIC # FinSight AI - Guía Completa de Uso de Agentes
# MAGIC
# MAGIC ## 🎯 Arquitectura
# MAGIC
# MAGIC ```
# MAGIC Usuario → Worker Agent → LLM con Tools → UC Functions → APIs Externas
# MAGIC                                               ↓
# MAGIC                                         Databricks Secrets
# MAGIC ```
# MAGIC
# MAGIC ### Componentes:
# MAGIC
# MAGIC 1. **Workers** (`src/agents/workers/`)
# MAGIC    - `MacroDataWorker`: Análisis macroeconómico
# MAGIC    - `MarketSentimentWorker`: Análisis de sentimiento de noticias
# MAGIC
# MAGIC 2. **UC Functions** (`main.finsight_ai` schema)
# MAGIC    - `get_gdp_data`: World Bank GDP data
# MAGIC    - `get_inflation_data`: World Bank inflation (CPI)
# MAGIC    - `get_unemployment_data`: World Bank unemployment
# MAGIC    - `get_interest_rate`: Interest rates (USA, placeholder)
# MAGIC    - `get_financial_news`: NewsAPI financial news
# MAGIC
# MAGIC 3. **Tool Wrappers** (`src/agents/tools/uc_functions.py`)
# MAGIC    - Convierte UC Functions en LangChain Tools
# MAGIC    - Maneja tool calling automático
# MAGIC
# MAGIC 4. **AI Gateway** (`main.finsight_ai.finsight-chat`)
# MAGIC    - LLM endpoint para los agentes
# MAGIC    - Maneja rate limiting y logging
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 📖 Ejemplos de Uso
# MAGIC
# MAGIC Este notebook muestra 3 formas de usar UC Functions:
# MAGIC
# MAGIC 1. **Tool Calling Automático** (Recomendado) - El LLM decide qué tools usar
# MAGIC 2. **Llamada Directa** - Control manual de UC Functions
# MAGIC 3. **LangGraph State Machine** - Flujo multi-step con estado
# MAGIC
# MAGIC ---

# COMMAND ----------

# DBTITLE 1,🛠️ Setup - Importar Workers
# Agregar el path del proyecto al sys.path
import sys
sys.path.append('/Workspace/Users/matiasadell@hotmail.com/agentic-ai-platform')

# Importar los workers
from src.agents.workers.macro_data_worker import MacroDataWorker
from src.agents.workers.market_sentiment_worker import MarketSentimentWorker

print("✅ Workers importados correctamente")
print("\nWorkers disponibles:")
print("  - MacroDataWorker: Análisis macroeconómico")
print("  - MarketSentimentWorker: Análisis de sentimiento de noticias")

# COMMAND ----------

# DBTITLE 1,📊 Ejemplo 1: MacroDataWorker - Tool Calling Automático
# EJEMPLO 1: Tool Calling Automático (Recomendado)
# El LLM decide qué UC Functions llamar

print("=" * 80)
print("EJEMPLO 1: MacroDataWorker con Tool Calling Automático")
print("=" * 80)

# Crear el worker
worker = MacroDataWorker()

# El LLM automáticamente:
# 1. Lee el query del usuario
# 2. Decide llamar get_gdp_data, get_inflation_data, get_unemployment_data
# 3. Recibe los resultados
# 4. Genera análisis

result = worker.analyze_economy("Argentina")

print("\n📈 Análisis Macroeconómico de Argentina:\n")
print(result)
print("\n" + "=" * 80)

# COMMAND ----------

# DBTITLE 1,🌍 Ejemplo 2: Comparación de Países
# EJEMPLO 2: Comparar múltiples países

print("\n" + "=" * 80)
print("EJEMPLO 2: Comparación de Países")
print("=" * 80)

# El LLM llamará get_gdp_data, get_inflation_data, etc. para cada país
comparison = worker.compare_countries(["Argentina", "Brazil", "Chile"])

print("\n🌎 Comparación Macroeconómica:\n")
print(comparison)
print("\n" + "=" * 80)

# COMMAND ----------

# DBTITLE 1,📰 Ejemplo 3: MarketSentimentWorker - Análisis de Noticias
# EJEMPLO 3: Análisis de Sentimiento con Noticias

print("\n" + "=" * 80)
print("EJEMPLO 3: Market Sentiment Worker")
print("=" * 80)

# Crear worker de sentiment
sentiment_worker = MarketSentimentWorker()

# El LLM llamará get_financial_news para buscar noticias
# Luego analizará el sentimiento

sentiment = sentiment_worker.analyze_sentiment(
    query="Tesla stock",
    days_back=7,
    max_articles=10
)

print("\n📊 Sentiment Analysis de Tesla:\n")
print(sentiment)
print("\n" + "=" * 80)

# COMMAND ----------

# DBTITLE 1,🔍 Ejemplo 4: Llamada Directa a UC Functions (Sin Tool Calling)
# EJEMPLO 4: Llamada Directa a UC Functions
# Para cuando quieres control manual total

from pyspark.sql import SparkSession
import json

print("\n" + "=" * 80)
print("EJEMPLO 4: Llamada Directa a UC Functions (Sin LLM)")
print("=" * 80)

spark = SparkSession.builder.getOrCreate()

# Llamar directamente la UC Function
print("\n1️⃣ Llamando get_gdp_data('USA')...\n")

result = spark.sql("""
    SELECT main.finsight_ai.get_gdp_data('USA')
""").collect()[0][0]

data = json.loads(result)

print(f"🇺🇸 GDP de {data['country']}:")
print(f"   Valor: ${data['gdp_usd']:,.0f}")
print(f"   Año: {data['year']}")
print(f"   Fuente: {data['source']}")

print("\n" + "=" * 80)

# COMMAND ----------

# DBTITLE 1,🗞️ Ejemplo 5: Llamada Directa a get_financial_news
# EJEMPLO 5: Llamada Directa a get_financial_news

from databricks.sdk.runtime import dbutils
from datetime import datetime, timedelta

print("\n" + "=" * 80)
print("EJEMPLO 5: Búsqueda Directa de Noticias")
print("=" * 80)

# Obtener API key de Databricks Secrets
api_key = dbutils.secrets.get(scope="finsight", key="NEWS_API_KEY")

# Calcular fechas
to_date = datetime.now().strftime("%Y-%m-%d")
from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

print(f"\n🔍 Buscando noticias de 'inflation' desde {from_date}...\n")

result = spark.sql(f"""
    SELECT main.finsight_ai.get_financial_news(
        '{api_key}',
        'inflation',
        '{from_date}',
        '{to_date}',
        'en',
        5
    )
""").collect()[0][0]

news_data = json.loads(result)

print(f"📰 Total de resultados: {news_data.get('total_results', 0)}")
print(f"\nTop {len(news_data.get('articles', []))} artículos:\n")

for i, article in enumerate(news_data.get('articles', []), 1):
    print(f"{i}. {article['title']}")
    print(f"   📌 Fuente: {article['source']}")
    print(f"   📅 Publicado: {article['published_at']}")
    print(f"   🔗 {article['url']}")
    print()

print("=" * 80)

# COMMAND ----------

# DBTITLE 1,📈 Ejemplo 6: Comparación de Sentimiento entre Acciones
# EJEMPLO 6: Comparar sentimiento de múltiples acciones

print("\n" + "=" * 80)
print("EJEMPLO 6: Comparación de Sentimiento - Tech Stocks")
print("=" * 80)

sentiment_worker = MarketSentimentWorker()

# El LLM llamará get_financial_news para cada stock
# Y comparará los sentimientos

comparison = sentiment_worker.compare_sentiment(
    queries=["Tesla stock", "Apple stock", "Microsoft stock"],
    days_back=7
)

print("\n💼 Comparación de Sentimientos:\n")
print(comparison)
print("\n" + "=" * 80)

# COMMAND ----------

# DBTITLE 1,🧪 Verificar UC Functions Disponibles
# MAGIC %sql
# MAGIC -- Verificar todas las UC Functions registradas en el schema
# MAGIC
# MAGIC SHOW FUNCTIONS IN main.finsight_ai;

# COMMAND ----------

# DBTITLE 1,✅ Test Individual de Cada UC Function
# MAGIC %sql
# MAGIC -- Test 1: GDP Data
# MAGIC SELECT main.finsight_ai.get_gdp_data('USA') as gdp_result;
# MAGIC
# MAGIC -- Test 2: Inflation Data  
# MAGIC SELECT main.finsight_ai.get_inflation_data('Argentina') as inflation_result;
# MAGIC
# MAGIC -- Test 3: Unemployment Data
# MAGIC SELECT main.finsight_ai.get_unemployment_data('Germany') as unemployment_result;
# MAGIC
# MAGIC -- Test 4: Interest Rate
# MAGIC SELECT main.finsight_ai.get_interest_rate('USA') as interest_result;

# COMMAND ----------

# DBTITLE 1,📚 Resumen - Cómo Funciona el Tool Calling
# MAGIC %md
# MAGIC # 🔄 Flujo Completo del Tool Calling
# MAGIC
# MAGIC ## 1️⃣ Sin Tool Calling (Manual)
# MAGIC
# MAGIC ```python
# MAGIC # Tu código llama directamente UC Function
# MAGIC spark.sql("SELECT main.finsight_ai.get_gdp_data('USA')")
# MAGIC ```
# MAGIC
# MAGIC **Pros:** Control total  
# MAGIC **Contras:** Tienes que escribir toda la lógica
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 2️⃣ Con Tool Calling Automático (Recomendado)
# MAGIC
# MAGIC ```python
# MAGIC worker = MacroDataWorker()
# MAGIC result = worker.analyze_economy("Argentina")
# MAGIC ```
# MAGIC
# MAGIC ### ¿Qué pasa internamente?
# MAGIC
# MAGIC 1. **Usuario** pregunta: "Analiza Argentina"
# MAGIC
# MAGIC 2. **LLM** recibe el query + lista de tools disponibles:
# MAGIC    ```
# MAGIC    Tools: [get_gdp_data, get_inflation_data, get_unemployment_data]
# MAGIC    ```
# MAGIC
# MAGIC 3. **LLM decide** qué tools llamar:
# MAGIC    ```json
# MAGIC    {
# MAGIC      "tool_calls": [
# MAGIC        {"name": "get_gdp_data", "args": {"country": "Argentina"}},
# MAGIC        {"name": "get_inflation_data", "args": {"country": "Argentina"}},
# MAGIC        {"name": "get_unemployment_data", "args": {"country": "Argentina"}}
# MAGIC      ]
# MAGIC    }
# MAGIC    ```
# MAGIC
# MAGIC 4. **LangChain** ejecuta cada tool:
# MAGIC    - `get_gdp_data` → llama `spark.sql("SELECT main.finsight_ai.get_gdp_data('Argentina')")`
# MAGIC    - `get_inflation_data` → llama `spark.sql("SELECT main.finsight_ai.get_inflation_data('Argentina')")`
# MAGIC    - etc.
# MAGIC
# MAGIC 5. **UC Functions** ejecutan:
# MAGIC    - Python code dentro de la función
# MAGIC    - Llamadas a APIs externas (World Bank, NewsAPI)
# MAGIC    - Retornan JSON
# MAGIC
# MAGIC 6. **Resultados** regresan al LLM:
# MAGIC    ```json
# MAGIC    [
# MAGIC      {"tool": "get_gdp_data", "result": {"gdp_usd": 640000000000, "year": "2023"}},
# MAGIC      {"tool": "get_inflation_data", "result": {"inflation_rate": 94.8, "year": "2023"}},
# MAGIC      {"tool": "get_unemployment_data", "result": {"unemployment_rate": 6.2, "year": "2023"}}
# MAGIC    ]
# MAGIC    ```
# MAGIC
# MAGIC 7. **LLM genera** respuesta final:
# MAGIC    > "Argentina's economy in 2023: GDP $640B, inflation 94.8% (very high), unemployment 6.2%..."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🎯 Ventajas del Tool Calling Automático
# MAGIC
# MAGIC ✅ **El LLM decide** qué datos necesita  
# MAGIC ✅ **Menos código** para ti  
# MAGIC ✅ **Más flexible** - puede llamar 1, 2, o N tools según necesidad  
# MAGIC ✅ **Natural** - escribes en lenguaje natural  
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🔧 Cuándo Usar Cada Approach
# MAGIC
# MAGIC | Scenario | Use | Reason |
# MAGIC |----------|-----|--------|
# MAGIC | Chat con usuario | Tool Calling | LLM decide qué preguntar |
# MAGIC | Pipeline ETL | Llamada Directa | Sabes exactamente qué datos necesitas |
# MAGIC | Exploración | Tool Calling | Quieres que el LLM explore |
# MAGIC | Reportes fijos | Llamada Directa | Mismos datos cada vez |
# MAGIC | Agente conversacional | Tool Calling | Diálogo multi-turn |
# MAGIC
# MAGIC ---