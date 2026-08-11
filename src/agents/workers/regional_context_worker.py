"""
Regional Context Worker
=======================

Agente especializado en análisis de contexto económico regional,
focalizando en Latinoamérica y mercados emergentes.

Capacidades:
- Búsqueda de noticias regionales (Tavily API)
- Análisis de políticas económicas regionales
- Comparación de indicadores macro entre países vecinos
- Detección de eventos regionales que afectan mercados

Uso:
    from src.agents.workers.regional_context_worker import RegionalContextWorker
    
    worker = RegionalContextWorker()
    result = worker.analyze_region("What's the economic situation in Argentina?")
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import HumanMessage
from databricks_langchain import ChatDatabricks


class RegionalContextWorker:
    """
    Worker para análisis de contexto económico regional.
    
    Utiliza Tavily API para búsqueda de información regional,
    World Bank API para datos macro comparativos, y LLM para síntesis.
    """
    
    def __init__(self):
        """Initialize Regional Context Worker."""
        self.llm = ChatDatabricks(
            endpoint="databricks-meta-llama-3-3-70b-instruct",
            temperature=0.1
        )
        
        # Import UC Function tools
        from src.agents.tools.uc_functions import (
            get_gdp_data,
            get_inflation_data,
            get_unemployment_data
        )
        
        # Try to import new regional tool
        try:
            from src.agents.tools.uc_functions import get_regional_news
            self.regional_tools = [get_regional_news]
        except ImportError:
            # Fallback if not yet registered
            print("⚠️  get_regional_news not yet available - using macro tools only")
            self.regional_tools = []
        
        self.macro_tools = [
            get_gdp_data,
            get_inflation_data,
            get_unemployment_data
        ]
        
        # Bind all tools to LLM
        all_tools = self.regional_tools + self.macro_tools
        self.llm_with_tools = self.llm.bind_tools(all_tools)
    
    def analyze_region(self, query: str, region: str = "Latin America") -> Dict[str, Any]:
        """
        Analiza el contexto económico regional basado en una query.
        
        Args:
            query: Pregunta del usuario (e.g., "What's happening in Argentina?")
            region: Región de interés (default: "Latin America")
        
        Returns:
            Dict con:
            - analysis: Análisis textual del contexto regional
            - data_sources: Lista de fuentes consultadas
            - key_findings: Hallazgos principales
            - timestamp: Timestamp de ejecución
        """
        print(f"\n🌍 Analyzing regional context: {region}")
        print(f"   Query: {query}")
        
        # Construct enhanced query for regional context
        enhanced_query = f"""
        Analyze the regional economic context for: {query}
        
        Focus on:
        1. Recent economic news and policy changes in {region}
        2. Comparative analysis with neighboring countries
        3. Regional trends affecting the market
        4. Key economic indicators (GDP, inflation, unemployment)
        
        Use available tools to gather data, then synthesize a comprehensive regional analysis.
        """
        
        try:
            # Invoke LLM with tools
            response = self.llm_with_tools.invoke([HumanMessage(content=enhanced_query)])
            
            return {
                "success": True,
                "analysis": response.content,
                "region": region,
                "query": query,
                "tool_calls": len(response.tool_calls) if hasattr(response, 'tool_calls') else 0,
                "timestamp": datetime.now().isoformat(),
                "worker": "RegionalContextWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "region": region,
                "timestamp": datetime.now().isoformat(),
                "worker": "RegionalContextWorker"
            }
    
    def compare_countries(
        self,
        countries: List[str],
        indicators: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compara indicadores económicos entre países de la región.
        
        Args:
            countries: Lista de países a comparar (e.g., ['Argentina', 'Brazil', 'Chile'])
            indicators: Lista de indicadores (default: ['gdp', 'inflation', 'unemployment'])
        
        Returns:
            Dict con comparación de indicadores entre países.
        """
        if indicators is None:
            indicators = ['gdp', 'inflation', 'unemployment']
        
        print(f"\n📊 Comparing countries: {', '.join(countries)}")
        print(f"   Indicators: {', '.join(indicators)}")
        
        query = f"""
        Compare the following economic indicators for these countries:
        
        Countries: {', '.join(countries)}
        Indicators: {', '.join(indicators)}
        
        For each country, retrieve:
        - GDP data
        - Inflation rate
        - Unemployment rate
        
        Then provide a comparative analysis highlighting:
        1. Which country has the strongest/weakest performance
        2. Notable trends or divergences
        3. Regional context and implications
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "comparison": response.content,
                "countries": countries,
                "indicators": indicators,
                "timestamp": datetime.now().isoformat(),
                "worker": "RegionalContextWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "countries": countries,
                "timestamp": datetime.now().isoformat(),
                "worker": "RegionalContextWorker"
            }
    
    def get_regional_trends(self, region: str, time_period: str = "last 30 days") -> Dict[str, Any]:
        """
        Identifica tendencias económicas regionales recientes.
        
        Args:
            region: Región (e.g., "Latin America", "South America")
            time_period: Período de análisis (default: "last 30 days")
        
        Returns:
            Dict con tendencias identificadas.
        """
        print(f"\n📈 Identifying regional trends: {region}")
        print(f"   Period: {time_period}")
        
        query = f"""
        Identify key economic trends in {region} over the {time_period}.
        
        Search for:
        1. Major policy changes or announcements
        2. Economic data releases and their impact
        3. Regional trade or cooperation developments
        4. Market reactions to regional events
        
        Provide a summary of the most significant trends and their implications.
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "trends": response.content,
                "region": region,
                "time_period": time_period,
                "timestamp": datetime.now().isoformat(),
                "worker": "RegionalContextWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "region": region,
                "timestamp": datetime.now().isoformat(),
                "worker": "RegionalContextWorker"
            }


# Example usage
if __name__ == "__main__":
    worker = RegionalContextWorker()
    
    # Example 1: Analyze Argentina's economic context
    result1 = worker.analyze_region(
        "What is the current economic situation in Argentina?",
        region="South America"
    )
    print("\n" + "="*80)
    print("REGIONAL ANALYSIS:")
    print(json.dumps(result1, indent=2))
    
    # Example 2: Compare countries
    result2 = worker.compare_countries(
        countries=["Argentina", "Brazil", "Chile"],
        indicators=["gdp", "inflation"]
    )
    print("\n" + "="*80)
    print("COUNTRY COMPARISON:")
    print(json.dumps(result2, indent=2))
