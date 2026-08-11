"""Sector News Worker - Specialized agent for sector-specific financial news analysis.

Capabilities:
- Sector-specific news analysis (tech, energy, finance, healthcare, etc.)
- Sector sentiment analysis
- Competitive tracking within sectors
- Trend detection (emerging vs established)
- Regulatory analysis by sector

Usage:
    from src.agents.workers.sector_news_worker import SectorNewsWorker
    
    worker = SectorNewsWorker()
    result = worker.analyze_sector_news(sector="technology", days=7)
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage
from databricks_langchain import ChatDatabricks


class SectorNewsWorker:
    """Worker for sector-specific financial news analysis.
    
    Analyzes news within specific sectors with sentiment analysis,
    competitive tracking, and trend detection.
    """
    
    # Supported sectors
    SECTORS = [
        'technology', 'energy', 'finance', 'healthcare', 
        'consumer', 'industrial', 'real_estate', 'materials',
        'telecommunications', 'utilities'
    ]
    
    def __init__(self):
        """Initialize Sector News Worker."""
        self.llm = ChatDatabricks(
            endpoint="databricks-meta-llama-3-3-70b-instruct",
            temperature=0.1
        )
        
        # Import UC Function tools
        try:
            from src.agents.tools.uc_functions import (
                get_financial_news,
                get_regional_news
            )
            self.news_tools = [get_financial_news, get_regional_news]
        except ImportError:
            print("⚠️  News tools not yet available")
            self.news_tools = []
        
        # Bind tools to LLM
        if self.news_tools:
            self.llm_with_tools = self.llm.bind_tools(self.news_tools)
        else:
            self.llm_with_tools = self.llm
    
    def analyze_sector_news(
        self,
        sector: str,
        days: int = 7,
        include_competitors: bool = True
    ) -> Dict[str, Any]:
        """Analyze news for a specific sector.
        
        Args:
            sector: Sector name (tech, energy, finance, etc.)
            days: Days to look back (default: 7)
            include_competitors: Include competitive analysis
        
        Returns:
            Dict with sector analysis, sentiment, companies, trends
        """
        if sector not in self.SECTORS:
            print(f"⚠️  Sector {sector} not in standard list. Using anyway...")
        
        keywords = self._get_sector_keywords(sector)
        
        print(f"\n🏭 Analyzing sector news: {sector}")
        print(f"   Period: last {days} days")
        print(f"   Keywords: {', '.join(keywords[:5])}")
        
        llm_query = f"""
        Analyze {sector} sector news from the last {days} days.
        
        Focus areas:
        1. Major sector developments and trends
        2. Key companies and competitive dynamics
        3. Regulatory changes affecting the sector
        4. Market sentiment and investor outlook
        5. Technology and innovation trends
        
        Provide:
        - Executive summary of sector news
        - Key companies mentioned and their news
        - Sentiment analysis (positive/negative/neutral trends)
        - Emerging themes and trends
        - Investment implications
        
        {"Include competitive analysis between major players." if include_competitors else ""}
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=llm_query)])
            
            return {
                "success": True,
                "analysis": response.content,
                "sector": sector,
                "days": days,
                "keywords": keywords,
                "tool_calls": len(response.tool_calls) if hasattr(response, 'tool_calls') else 0,
                "timestamp": datetime.now().isoformat(),
                "worker": "SectorNewsWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sector": sector,
                "timestamp": datetime.now().isoformat(),
                "worker": "SectorNewsWorker"
            }
    
    def compare_sector_sentiment(
        self,
        sectors: List[str],
        days: int = 7
    ) -> Dict[str, Any]:
        """Compare sentiment across multiple sectors.
        
        Args:
            sectors: List of sector names to compare
            days: Days to look back
        
        Returns:
            Dict with cross-sector sentiment comparison
        """
        print(f"\n📊 Comparing sector sentiment")
        print(f"   Sectors: {', '.join(sectors)}")
        print(f"   Period: last {days} days")
        
        llm_query = f"""
        Compare news sentiment across these sectors: {', '.join(sectors)}
        
        For each sector, analyze:
        1. Overall sentiment (positive/negative/neutral)
        2. Major news themes
        3. Investor outlook
        4. Relative performance vs other sectors
        
        Then provide:
        - Sentiment ranking (most positive to most negative)
        - Cross-sector themes and connections
        - Relative investment attractiveness
        - Risk factors by sector
        
        Period: last {days} days
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=llm_query)])
            
            return {
                "success": True,
                "comparison": response.content,
                "sectors": sectors,
                "days": days,
                "timestamp": datetime.now().isoformat(),
                "worker": "SectorNewsWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sectors": sectors,
                "timestamp": datetime.now().isoformat(),
                "worker": "SectorNewsWorker"
            }
    
    def detect_sector_trends(
        self,
        sector: str,
        days: int = 14
    ) -> Dict[str, Any]:
        """Detect emerging trends in a sector.
        
        Args:
            sector: Sector name
            days: Days to look back (default: 14)
        
        Returns:
            Dict with detected trends and momentum
        """
        print(f"\n📈 Detecting trends in {sector} sector")
        print(f"   Period: last {days} days")
        
        llm_query = f"""
        Detect and analyze emerging trends in the {sector} sector.
        
        Look for:
        1. New technologies or innovations gaining traction
        2. Regulatory or policy shifts
        3. Market dynamics changes
        4. Consumer behavior trends
        5. Competitive landscape shifts
        
        For each trend:
        - Description and evidence
        - Momentum (emerging vs established)
        - Potential impact (high/medium/low)
        - Key players driving the trend
        - Investment implications
        
        Period: last {days} days
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=llm_query)])
            
            return {
                "success": True,
                "trends": response.content,
                "sector": sector,
                "days": days,
                "timestamp": datetime.now().isoformat(),
                "worker": "SectorNewsWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sector": sector,
                "timestamp": datetime.now().isoformat(),
                "worker": "SectorNewsWorker"
            }
    
    def _get_sector_keywords(self, sector: str) -> List[str]:
        """Get keywords for sector-specific searches."""
        keywords_map = {
            'technology': ['tech', 'software', 'hardware', 'AI', 'cloud', 'semiconductor'],
            'energy': ['oil', 'gas', 'renewable', 'solar', 'wind', 'electricity'],
            'finance': ['bank', 'fintech', 'insurance', 'lending', 'payment'],
            'healthcare': ['pharma', 'biotech', 'medical', 'hospital', 'drug'],
            'consumer': ['retail', 'consumer goods', 'ecommerce', 'brands'],
            'industrial': ['manufacturing', 'machinery', 'construction', 'aerospace'],
            'real_estate': ['property', 'REIT', 'commercial real estate', 'housing'],
            'materials': ['mining', 'metals', 'chemicals', 'commodities'],
            'telecommunications': ['telecom', '5G', 'wireless', 'broadband'],
            'utilities': ['utility', 'water', 'electric utility', 'infrastructure']
        }
        
        return keywords_map.get(sector, [sector])
