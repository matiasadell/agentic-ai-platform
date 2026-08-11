"""
Event Detection Worker
======================

Agente especializado en detección de eventos corporativos materiales
y eventos que mueven el mercado.

Capacidades:
- Detección de earnings reports y fechas de publicación (Alpha Vantage)
- Identificación de M&A, adquisiciones, fusiones (NewsAPI)
- Eventos regulatorios y cambios de management
- Análisis de impacto en precios

Uso:
    from src.agents.workers.event_detection_worker import EventDetectionWorker
    
    worker = EventDetectionWorker()
    result = worker.detect_events("AAPL")
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage
from databricks_langchain import ChatDatabricks


class EventDetectionWorker:
    """
    Worker para detección de eventos corporativos y materiales.
    
    Utiliza Alpha Vantage para datos de earnings y NewsAPI para
    eventos de mercado, con LLM para clasificación e interpretación.
    """
    
    def __init__(self):
        """Initialize Event Detection Worker."""
        self.llm = ChatDatabricks(
            endpoint="databricks-meta-llama-3-3-70b-instruct",
            temperature=0.1
        )
        
        # Import UC Function tools
        try:
            from src.agents.tools.uc_functions import (
                detect_corporate_events,
                get_financial_news
            )
            self.event_tools = [detect_corporate_events, get_financial_news]
        except ImportError:
            # Fallback if tools not yet registered
            print("⚠️  Event detection tools not yet available")
            self.event_tools = []
        
        # Bind tools to LLM
        if self.event_tools:
            self.llm_with_tools = self.llm.bind_tools(self.event_tools)
        else:
            self.llm_with_tools = self.llm
    
    def detect_events(
        self,
        symbol: str,
        event_types: List[str] = None,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Detecta eventos corporativos materiales para una acción.
        
        Args:
            symbol: Símbolo del ticker (e.g., 'AAPL', 'TSLA')
            event_types: Tipos de eventos ('earnings', 'M&A', 'regulatory', 'management')
            lookback_days: Días hacia atrás para buscar (default: 30)
        
        Returns:
            Dict con:
            - events: Lista de eventos detectados
            - classification: Clasificación por tipo de evento
            - impact_analysis: Análisis de impacto en precio
            - upcoming_events: Eventos futuros programados
            - timestamp: Timestamp de ejecución
        """
        if event_types is None:
            event_types = ['earnings', 'M&A', 'regulatory', 'management']
        
        print(f"\n⚡ Detecting events for: {symbol}")
        print(f"   Event types: {', '.join(event_types)}")
        print(f"   Lookback: {lookback_days} days")
        
        query = f"""
        Detect and analyze corporate events for {symbol}:
        
        1. Get upcoming earnings dates and recent reports
        2. Search for recent news covering:
           - Earnings announcements
           - Mergers & Acquisitions
           - Regulatory changes
           - Management changes
           - Product launches
           - Legal issues
        
        3. For each event found:
           - Classify event type
           - Assess materiality (High/Medium/Low)
           - Analyze market impact (if price data available)
        
        4. Provide:
           - Timeline of recent material events
           - Upcoming scheduled events
           - Risk assessment
        
        Focus on events from the last {lookback_days} days.
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "analysis": response.content,
                "symbol": symbol,
                "event_types": event_types,
                "lookback_days": lookback_days,
                "tool_calls": len(response.tool_calls) if hasattr(response, 'tool_calls') else 0,
                "timestamp": datetime.now().isoformat(),
                "worker": "EventDetectionWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "worker": "EventDetectionWorker"
            }
    
    def get_earnings_calendar(
        self,
        symbols: List[str]
    ) -> Dict[str, Any]:
        """
        Obtiene el calendario de earnings para múltiples acciones.
        
        Args:
            symbols: Lista de símbolos (e.g., ['AAPL', 'MSFT', 'GOOGL'])
        
        Returns:
            Dict con calendario de earnings.
        """
        print(f"\n📅 Getting earnings calendar for: {', '.join(symbols)}")
        
        query = f"""
        Get the earnings calendar for these stocks: {', '.join(symbols)}
        
        For each stock:
        1. Retrieve upcoming earnings date
        2. Get last reported quarter
        3. Identify fiscal period
        
        Present in calendar format, sorted by date.
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "calendar": response.content,
                "symbols": symbols,
                "timestamp": datetime.now().isoformat(),
                "worker": "EventDetectionWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbols": symbols,
                "timestamp": datetime.now().isoformat(),
                "worker": "EventDetectionWorker"
            }
    
    def detect_market_moving_news(
        self,
        query: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Detecta noticias que mueven el mercado según un tema específico.
        
        Args:
            query: Tema de búsqueda (e.g., 'Federal Reserve rate decision', 'OPEC meeting')
            days: Días hacia atrás (default: 7)
        
        Returns:
            Dict con noticias y análisis de impacto.
        """
        print(f"\n📢 Detecting market-moving news: {query}")
        print(f"   Period: last {days} days")
        
        llm_query = f"""
        Search for market-moving news related to: {query}
        
        1. Find recent news articles (last {days} days)
        2. Filter for material/significant events
        3. Analyze:
           - Event description and timing
           - Expected market impact
           - Affected sectors/stocks
           - Historical precedent (if applicable)
        
        Provide a summary of the most significant market-moving events.
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=llm_query)])
            
            return {
                "success": True,
                "news_analysis": response.content,
                "query": query,
                "days": days,
                "timestamp": datetime.now().isoformat(),
                "worker": "EventDetectionWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "worker": "EventDetectionWorker"
            }
    
    def analyze_event_impact(
        self,
        symbol: str,
        event_description: str,
        event_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza el impacto de un evento específico en el precio de una acción.
        
        Args:
            symbol: Símbolo del ticker
            event_description: Descripción del evento (e.g., 'Q3 earnings beat')
            event_date: Fecha del evento en YYYY-MM-DD (optional)
        
        Returns:
            Dict con análisis de impacto.
        """
        print(f"\n📊 Analyzing event impact for {symbol}")
        print(f"   Event: {event_description}")
        if event_date:
            print(f"   Date: {event_date}")
        
        query = f"""
        Analyze the market impact of this event:
        
        Stock: {symbol}
        Event: {event_description}
        {f'Date: {event_date}' if event_date else ''}
        
        1. Search for news about this specific event
        2. If event_date provided, analyze price movement around that date
        3. Assess:
           - Immediate market reaction
           - Sentiment (positive/negative/neutral)
           - Magnitude of impact (significant/moderate/minimal)
           - Duration of impact (sustained vs. temporary)
        
        4. Provide context: How does this compare to similar events?
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "impact_analysis": response.content,
                "symbol": symbol,
                "event": event_description,
                "event_date": event_date,
                "timestamp": datetime.now().isoformat(),
                "worker": "EventDetectionWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "worker": "EventDetectionWorker"
            }


# Example usage
if __name__ == "__main__":
    worker = EventDetectionWorker()
    
    # Example 1: Detect events for Apple
    result1 = worker.detect_events(
        symbol="AAPL",
        event_types=['earnings', 'M&A', 'product'],
        lookback_days=30
    )
    print("\n" + "="*80)
    print("EVENT DETECTION:")
    print(json.dumps(result1, indent=2))
    
    # Example 2: Earnings calendar
    result2 = worker.get_earnings_calendar(
        symbols=["AAPL", "MSFT", "TSLA"]
    )
    print("\n" + "="*80)
    print("EARNINGS CALENDAR:")
    print(json.dumps(result2, indent=2))
    
    # Example 3: Market-moving news
    result3 = worker.detect_market_moving_news(
        "Federal Reserve interest rate decision",
        days=7
    )
    print("\n" + "="*80)
    print("MARKET-MOVING NEWS:")
    print(json.dumps(result3, indent=2))
