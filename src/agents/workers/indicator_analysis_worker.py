"""
Indicator Analysis Worker
=========================

Agente especializado en análisis técnico de indicadores financieros,
precios de acciones, y detección de tendencias.

Capacidades:
- Obtención de precios históricos (Yahoo Finance)
- Cálculo de indicadores técnicos: RSI, MACD, SMA, EMA, Bollinger Bands (Alpha Vantage)
- Identificación de patrones y tendencias
- Análisis de soporte y resistencia

Uso:
    from src.agents.workers.indicator_analysis_worker import IndicatorAnalysisWorker
    
    worker = IndicatorAnalysisWorker()
    result = worker.analyze_stock("AAPL", indicators=["RSI", "MACD"])
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage
from databricks_langchain import ChatDatabricks


class IndicatorAnalysisWorker:
    """
    Worker para análisis técnico de acciones e indicadores financieros.
    
    Utiliza Yahoo Finance para precios históricos y Alpha Vantage para indicadores
    técnicos, con LLM para síntesis e interpretación.
    """
    
    def __init__(self):
        """Initialize Indicator Analysis Worker."""
        self.llm = ChatDatabricks(
            endpoint="databricks-meta-llama-3-3-70b-instruct",
            temperature=0.1
        )
        
        # Import UC Function tools
        try:
            from src.agents.tools.uc_functions import (
                get_stock_prices,
                get_technical_indicators
            )
            self.technical_tools = [get_stock_prices, get_technical_indicators]
        except ImportError:
            # Fallback if tools not yet registered
            print("⚠️  Technical indicator tools not yet available")
            self.technical_tools = []
        
        # Bind tools to LLM
        if self.technical_tools:
            self.llm_with_tools = self.llm.bind_tools(self.technical_tools)
        else:
            self.llm_with_tools = self.llm
    
    def analyze_stock(
        self,
        symbol: str,
        indicators: List[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Realiza análisis técnico completo de una acción.
        
        Args:
            symbol: Símbolo del ticker (e.g., 'AAPL', 'TSLA', 'GGAL.BA')
            indicators: Lista de indicadores a calcular (default: ['RSI', 'MACD'])
            days: Días de datos históricos (default: 30)
        
        Returns:
            Dict con:
            - analysis: Análisis textual de los indicadores
            - price_data: Datos de precios históricos
            - technical_indicators: Indicadores calculados
            - recommendation: Recomendación (Buy/Hold/Sell)
            - timestamp: Timestamp de ejecución
        """
        if indicators is None:
            indicators = ['RSI', 'MACD']
        
        print(f"\n📈 Analyzing stock: {symbol}")
        print(f"   Indicators: {', '.join(indicators)}")
        print(f"   Period: {days} days")
        
        query = f"""
        Perform a comprehensive technical analysis for {symbol}:
        
        1. Get historical price data for the last {days} days
        2. Calculate the following technical indicators: {', '.join(indicators)}
        3. Analyze trends:
           - Current price momentum
           - Support and resistance levels
           - Indicator signals (overbought/oversold, bullish/bearish)
        4. Provide a trading recommendation (Buy/Hold/Sell) with justification
        
        Use available tools to gather data, then synthesize a technical analysis.
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "analysis": response.content,
                "symbol": symbol,
                "indicators_requested": indicators,
                "days": days,
                "tool_calls": len(response.tool_calls) if hasattr(response, 'tool_calls') else 0,
                "timestamp": datetime.now().isoformat(),
                "worker": "IndicatorAnalysisWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "worker": "IndicatorAnalysisWorker"
            }
    
    def compare_stocks(
        self,
        symbols: List[str],
        indicator: str = "RSI",
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Compara múltiples acciones según un indicador específico.
        
        Args:
            symbols: Lista de símbolos (e.g., ['AAPL', 'MSFT', 'GOOGL'])
            indicator: Indicador a comparar (default: 'RSI')
            days: Período de análisis (default: 30)
        
        Returns:
            Dict con comparación entre acciones.
        """
        print(f"\n🔍 Comparing stocks: {', '.join(symbols)}")
        print(f"   Indicator: {indicator}")
        print(f"   Period: {days} days")
        
        query = f"""
        Compare the following stocks using {indicator} indicator:
        
        Stocks: {', '.join(symbols)}
        Period: {days} days
        
        For each stock:
        1. Get price data
        2. Calculate {indicator}
        3. Compare current readings
        
        Then provide:
        - Which stock shows the strongest technical signal
        - Relative strength ranking
        - Trading opportunities identified
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "comparison": response.content,
                "symbols": symbols,
                "indicator": indicator,
                "days": days,
                "timestamp": datetime.now().isoformat(),
                "worker": "IndicatorAnalysisWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbols": symbols,
                "timestamp": datetime.now().isoformat(),
                "worker": "IndicatorAnalysisWorker"
            }
    
    def detect_patterns(
        self,
        symbol: str,
        pattern_type: str = "trend",
        days: int = 60
    ) -> Dict[str, Any]:
        """
        Detecta patrones técnicos en el precio (golden cross, death cross, breakouts).
        
        Args:
            symbol: Símbolo del ticker
            pattern_type: Tipo de patrón ('trend', 'reversal', 'breakout')
            days: Período de análisis (default: 60)
        
        Returns:
            Dict con patrones identificados.
        """
        print(f"\n🔎 Detecting patterns: {symbol}")
        print(f"   Pattern type: {pattern_type}")
        print(f"   Period: {days} days")
        
        query = f"""
        Analyze {symbol} for {pattern_type} patterns over the last {days} days:
        
        1. Get historical price data
        2. Calculate moving averages (SMA 50, SMA 200)
        3. Identify patterns:
           - Golden Cross (bullish)
           - Death Cross (bearish)
           - Breakouts above resistance
           - Breakdowns below support
        
        Report any significant patterns detected and their implications.
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "patterns": response.content,
                "symbol": symbol,
                "pattern_type": pattern_type,
                "days": days,
                "timestamp": datetime.now().isoformat(),
                "worker": "IndicatorAnalysisWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "worker": "IndicatorAnalysisWorker"
            }
    
    def get_momentum_analysis(
        self,
        symbol: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Análisis de momentum: velocidad y dirección del movimiento de precios.
        
        Args:
            symbol: Símbolo del ticker
            days: Período (default: 30)
        
        Returns:
            Dict con análisis de momentum.
        """
        print(f"\n⚡ Momentum analysis: {symbol}")
        print(f"   Period: {days} days")
        
        query = f"""
        Analyze price momentum for {symbol} over {days} days:
        
        1. Get price data and calculate:
           - RSI (Relative Strength Index)
           - MACD (Moving Average Convergence Divergence)
        
        2. Evaluate momentum:
           - Is the stock gaining or losing momentum?
           - Are we in overbought or oversold territory?
           - MACD signals (bullish/bearish crossovers)
        
        3. Provide momentum rating: Strong/Moderate/Weak, Bullish/Bearish
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=query)])
            
            return {
                "success": True,
                "momentum_analysis": response.content,
                "symbol": symbol,
                "days": days,
                "timestamp": datetime.now().isoformat(),
                "worker": "IndicatorAnalysisWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "worker": "IndicatorAnalysisWorker"
            }


# Example usage
if __name__ == "__main__":
    worker = IndicatorAnalysisWorker()
    
    # Example 1: Analyze Apple stock
    result1 = worker.analyze_stock(
        symbol="AAPL",
        indicators=["RSI", "MACD"],
        days=30
    )
    print("\n" + "="*80)
    print("STOCK ANALYSIS:")
    print(json.dumps(result1, indent=2))
    
    # Example 2: Compare tech stocks
    result2 = worker.compare_stocks(
        symbols=["AAPL", "MSFT", "GOOGL"],
        indicator="RSI",
        days=30
    )
    print("\n" + "="*80)
    print("STOCK COMPARISON:")
    print(json.dumps(result2, indent=2))
    
    # Example 3: Momentum analysis
    result3 = worker.get_momentum_analysis("TSLA", days=30)
    print("\n" + "="*80)
    print("MOMENTUM ANALYSIS:")
    print(json.dumps(result3, indent=2))
