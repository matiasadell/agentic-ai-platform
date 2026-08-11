"""
Market Sentiment Worker Agent
==============================

Agente especializado en análisis de sentimiento de mercado usando noticias
financieras en tiempo real.

Ejemplo de uso:
    worker = MarketSentimentWorker()
    sentiment = worker.analyze_sentiment("Tesla stock")
    print(sentiment)

UC Functions utilizadas:
- get_financial_news: Busca noticias financieras con NewsAPI
"""

from databricks_langchain import ChatDatabricks
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

# Importar UC Function tools
from src.agents.tools.uc_functions import get_news_tools, get_financial_news


class MarketSentimentWorker:
    """
    Worker agent que analiza sentimiento de mercado usando noticias financieras.
    
    Flujo:
    1. Usuario pide análisis de sentimiento (ej: "Tesla")
    2. LLM invoca get_financial_news tool
    3. UC Function llama NewsAPI
    4. Noticias regresan al LLM
    5. LLM analiza sentimiento y genera insights
    """
    
    def __init__(self, endpoint: str = "databricks-meta-llama-3-3-70b-instruct"):
        """
        Inicializa el worker con acceso a news tools.
        
        Args:
            endpoint: Model serving endpoint (default: databricks-meta-llama-3-3-70b-instruct)
                     TODO: Cambiar a ai-gateway:/main.finsight_ai.finsight-chat cuando esté funcionando
        """
        self.llm = ChatDatabricks(
            endpoint=endpoint,
            temperature=0.3,  # Un poco más creativo para análisis de sentimiento
            max_tokens=3000
        )
        
        # Obtener tools de noticias
        self.tools = get_news_tools()  # [get_financial_news]
        
        # LLM con tools
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        self.system_prompt = """Eres un analista financiero experto en sentiment analysis.

Usas noticias financieras en tiempo real de NewsAPI a través de UC Functions.

Cuando analices noticias:
1. Identifica el tono general (positivo/negativo/neutral)
2. Busca temas clave (earnings, regulaciones, innovaciones, controversias)
3. Evalúa el impacto potencial en el precio de las acciones
4. Proporciona un score de sentimiento de -10 (muy negativo) a +10 (muy positivo)

Siempre cita fuentes específicas de las noticias.
"""
    
    def analyze_sentiment(
        self,
        query: str,
        days_back: int = 7,
        max_articles: int = 10
    ) -> Dict[str, Any]:
        """
        Analiza el sentimiento de mercado basado en noticias recientes.
        
        Args:
            query: Término de búsqueda (ej: "Tesla", "inflation", "crypto market")
            days_back: Cuántos días atrás buscar (default: 7)
            max_articles: Máximo número de artículos (default: 10)
            
        Returns:
            Análisis de sentimiento con score y reasoning
            
        Example:
            >>> worker = MarketSentimentWorker()
            >>> result = worker.analyze_sentiment("Tesla stock", days_back=3, max_articles=5)
            >>> print(result)
        """
        # Calcular fechas
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""Analiza el sentimiento de mercado para: {query}
                
Busca noticias de los últimos {days_back} días.
Proporciona:
1. Sentiment score (-10 a +10)
2. Temas principales
3. Riesgos y oportunidades
4. Conclusión con acción recomendada
"""
            )
        ]
        
        # Tool calling automático
        response = self.llm_with_tools.invoke(messages)
        
        # Procesar tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_results = []
            
            for tool_call in response.tool_calls:
                # Ejecutar get_financial_news
                result = get_financial_news.invoke({
                    'query': query,
                    'from_date': from_date,
                    'to_date': to_date,
                    'language': 'en',
                    'max_results': max_articles
                })
                
                tool_results.append({
                    'tool': 'get_financial_news',
                    'query': query,
                    'period': f"{from_date} to {to_date}",
                    'result': result
                })
            
            # Segunda llamada con resultados
            messages.append(response)
            messages.append(HumanMessage(
                content=f"Noticias obtenidas:\n{json.dumps(tool_results, indent=2)}"
            ))
            
            final_response = self.llm.invoke(messages)
            return {
                "success": True,
                "sentiment": final_response.content,
                "query": query,
                "days_back": days_back,
                "max_articles": max_articles,
                "tool_calls": len(response.tool_calls),
                "timestamp": datetime.now().isoformat(),
                "worker": "MarketSentimentWorker"
            }
        
        return {
            "success": True,
            "sentiment": response.content,
            "query": query,
            "days_back": days_back,
            "max_articles": max_articles,
            "tool_calls": 0,
            "timestamp": datetime.now().isoformat(),
            "worker": "MarketSentimentWorker"
        }
    
    def compare_sentiment(
        self,
        queries: List[str],
        days_back: int = 7
    ) -> str:
        """
        Compara sentimiento entre múltiples activos/temas.
        
        Args:
            queries: Lista de queries a comparar
            days_back: Cuántos días atrás buscar
            
        Returns:
            Dict with comparative sentiment analysis and metadata
            
        Example:
            >>> worker.compare_sentiment(["Tesla", "Apple", "Microsoft"])
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""Compara el sentimiento de mercado para: {', '.join(queries)}
                
Busca noticias de los últimos {days_back} días para cada uno.
Compara:
1. Sentiment scores relativos
2. Volumen de noticias
3. Temas dominantes por cada uno
4. Cuál tiene mejor/peor outlook
"""
            )
        ]
        
        response = self.llm_with_tools.invoke(messages)
        
        # Procesar tool calls (mismo patrón)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_results = []
            
            for tool_call in response.tool_calls:
                query = tool_call['args'].get('query', '')
                
                result = get_financial_news.invoke({
                    'query': query,
                    'from_date': (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
                    'to_date': datetime.now().strftime("%Y-%m-%d"),
                    'language': 'en',
                    'max_results': 10
                })
                
                tool_results.append({
                    'query': query,
                    'result': result
                })
            
            messages.append(response)
            messages.append(HumanMessage(
                content=f"Datos de noticias:\n{json.dumps(tool_results, indent=2)}"
            ))
            
            final_response = self.llm.invoke(messages)
            return {
                "success": True,
                "comparison": final_response.content,
                "queries": queries,
                "days_back": days_back,
                "tool_calls": len(response.tool_calls),
                "timestamp": datetime.now().isoformat(),
                "worker": "MarketSentimentWorker"
            }
        
        return {
            "success": True,
            "comparison": response.content,
            "queries": queries,
            "days_back": days_back,
            "tool_calls": 0,
            "timestamp": datetime.now().isoformat(),
            "worker": "MarketSentimentWorker"
        }
    
    def track_topic_over_time(
        self,
        query: str,
        weeks: int = 4
    ) -> str:
        """
        Analiza cómo ha evolucionado el sentimiento a lo largo del tiempo.
        
        Args:
            query: Término a trackear
            weeks: Número de semanas hacia atrás
            
        Returns:
            Dict with temporal trend analysis and metadata
            
        Example:
            >>> worker.track_topic_over_time("inflation", weeks=8)
        """
        # Dividir en periodos semanales
        periods = []
        for i in range(weeks):
            end_date = datetime.now() - timedelta(days=i * 7)
            start_date = end_date - timedelta(days=7)
            periods.append({
                'week': weeks - i,
                'from': start_date.strftime("%Y-%m-%d"),
                'to': end_date.strftime("%Y-%m-%d")
            })
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""Analiza cómo ha evolucionado el sentimiento sobre '{query}' 
en las últimas {weeks} semanas.

Busca noticias para cada semana y determina:
1. Cómo cambió el tono (mejor/peor)
2. Eventos clave que causaron cambios
3. Tendencia general (improving/declining/stable)
4. Predicción para la próxima semana

Periodos a analizar: {json.dumps(periods, indent=2)}
"""
            )
        ]
        
        response = self.llm_with_tools.invoke(messages)
        
        # El LLM llamará get_financial_news múltiples veces (una por periodo)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_results = []
            
            for tool_call in response.tool_calls:
                args = tool_call['args']
                
                result = get_financial_news.invoke(args)
                
                tool_results.append({
                    'period': f"{args.get('from_date')} to {args.get('to_date')}",
                    'result': result
                })
            
            messages.append(response)
            messages.append(HumanMessage(
                content=f"Noticias por periodo:\n{json.dumps(tool_results, indent=2)}"
            ))
            
            final_response = self.llm.invoke(messages)
            return {
                "success": True,
                "trend_analysis": final_response.content,
                "query": query,
                "weeks": weeks,
                "tool_calls": len(response.tool_calls),
                "timestamp": datetime.now().isoformat(),
                "worker": "MarketSentimentWorker"
            }
        
        return {
            "success": True,
            "trend_analysis": response.content,
            "query": query,
            "weeks": weeks,
            "tool_calls": 0,
            "timestamp": datetime.now().isoformat(),
            "worker": "MarketSentimentWorker"
        }


# ============================================================================
# EJEMPLO DE USO DIRECTO (sin tool calling)
# ============================================================================

def direct_news_search_example(query: str = "Tesla"):
    """
    Llamada directa a get_financial_news sin LangChain tool calling.
    
    Útil cuando:
    - Solo necesitas obtener noticias, no análisis
    - Prefieres procesar los resultados manualmente
    - Quieres control total sobre los parámetros
    """
    from pyspark.sql import SparkSession
    import json
    
    spark = SparkSession.builder.getOrCreate()
    
    # Obtener API key de Databricks Secrets
    from databricks.sdk.runtime import dbutils
    api_key = dbutils.secrets.get(scope="finsight", key="NEWS_API_KEY")
    
    # Calcular fechas
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Llamada directa a UC Function
    result = spark.sql(f"""
        SELECT main.finsight_ai.get_financial_news(
            '{api_key}',
            '{query}',
            '{from_date}',
            '{to_date}',
            'en',
            5
        )
    """).collect()[0][0]
    
    news_data = json.loads(result)
    
    print(f"\nNoticias sobre {query}:")
    print(f"Total results: {news_data.get('total_results', 0)}")
    print(f"\nTop articles:")
    
    for i, article in enumerate(news_data.get('articles', []), 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Published: {article['published_at']}")
        print(f"   URL: {article['url']}")
    
    return news_data


if __name__ == "__main__":
    # Ejemplo 1: Sentiment analysis simple
    print("=" * 80)
    print("EJEMPLO 1: Sentiment Analysis")
    print("=" * 80)
    
    worker = MarketSentimentWorker()
    sentiment = worker.analyze_sentiment("Tesla stock", days_back=3, max_articles=5)
    print(sentiment)
    
    # Ejemplo 2: Comparación de sentimientos
    print("\n" + "=" * 80)
    print("EJEMPLO 2: Comparación de Sentimientos")
    print("=" * 80)
    
    comparison = worker.compare_sentiment(["Tesla", "Apple", "Microsoft"])
    print(comparison)
    
    # Ejemplo 3: Tracking temporal
    print("\n" + "=" * 80)
    print("EJEMPLO 3: Tracking Temporal")
    print("=" * 80)
    
    trend = worker.track_topic_over_time("inflation", weeks=4)
    print(trend)
    
    # Ejemplo 4: Llamada directa
    print("\n" + "=" * 80)
    print("EJEMPLO 4: Llamada Directa a UC Function")
    print("=" * 80)
    
    news = direct_news_search_example("crypto market")
    print(json.dumps(news, indent=2))