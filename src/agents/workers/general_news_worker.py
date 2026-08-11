"""General News Worker - Specialized agent for batch financial news ingestion and analysis.

Capabilities:
- Batch news ingestion from multiple sources (NewsAPI)
- Relevance and quality filtering  
- Automatic categorization (earnings, policy, market, corporate, etc.)
- Multi-source news aggregation
- Event timeline creation

Usage:
    from src.agents.workers.news.general_news_worker import GeneralNewsWorker
    
    worker = GeneralNewsWorker()
    result = worker.aggregate_news(query="financial markets", days=7)
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage
from databricks_langchain import ChatDatabricks


class GeneralNewsWorker:
    """Worker for batch financial news ingestion and analysis.
    
    Uses NewsAPI for news search and LLM for filtering,
    categorization, and synthesis.
    """
    
    def __init__(self):
        """Initialize General News Worker."""
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
    
    def aggregate_news(
        self,
        query: str,
        days: int = 7,
        categories: List[str] = None
    ) -> Dict[str, Any]:
        """Aggregate financial news from multiple sources.
        
        Args:
            query: Search topic (e.g., 'financial markets', 'banking sector')
            days: Days to look back (default: 7)
            categories: Specific categories to filter
        
        Returns:
            Dict with news summary, categories, timeline, key themes, timestamp
        """
        if categories is None:
            categories = ['earnings', 'policy', 'market', 'corporate', 'regulatory']
        
        print(f"\n📰 Aggregating news for: {query}")
        print(f"   Period: last {days} days")
        print(f"   Categories: {', '.join(categories)}")
        
        llm_query = f"""
        Aggregate and analyze financial news related to: {query}
        
        1. Search for news from the last {days} days
        2. Filter for relevant and high-quality articles
        3. Categorize articles into: {', '.join(categories)}
        4. Identify key themes and trends
        5. Create a timeline of major events
        
        Provide:
        - Summary of major news and developments
        - Category breakdown
        - Timeline of key events (chronological)
        - Emerging themes and trends
        - Notable sources and their perspectives
        
        Focus on material and actionable information.
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=llm_query)])
            
            return {
                "success": True,
                "analysis": response.content,
                "query": query,
                "days": days,
                "categories": categories,
                "tool_calls": len(response.tool_calls) if hasattr(response, 'tool_calls') else 0,
                "timestamp": datetime.now().isoformat(),
                "worker": "GeneralNewsWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "worker": "GeneralNewsWorker"
            }
    
    def create_news_timeline(
        self,
        query: str,
        days: int = 14
    ) -> Dict[str, Any]:
        """Create a chronological timeline of major news.
        
        Args:
            query: Search topic
            days: Days to look back (default: 14)
        
        Returns:
            Dict with timeline of events
        """
        print(f"\n📅 Creating news timeline: {query}")
        print(f"   Period: last {days} days")
        
        llm_query = f"""
        Create a chronological timeline of major financial news for: {query}
        
        1. Search news from the last {days} days
        2. Identify major events and announcements
        3. Organize chronologically (most recent first)
        4. For each event:
           - Date and time
           - Event description
           - Market impact
           - Follow-up developments
        
        Present as a clear, date-based timeline.
        """
        
        try:
            response = self.llm_with_tools.invoke([HumanMessage(content=llm_query)])
            
            return {
                "success": True,
                "timeline": response.content,
                "query": query,
                "days": days,
                "timestamp": datetime.now().isoformat(),
                "worker": "GeneralNewsWorker"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "worker": "GeneralNewsWorker"
            }
