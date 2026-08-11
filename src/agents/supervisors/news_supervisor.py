"""NewsSupervisor - Level 2 supervisor for News domain.

Coordinates 4 News Workers:
- GeneralNewsWorker: Batch news ingestion, filtering, categorization
- SectorNewsWorker: Sector-specific analysis, sentiment, trends
- MarketSentimentWorker: Market sentiment analysis, fear/greed index
- EventDetectionWorker: Corporate events detection (earnings, M&A, IPOs)

Capabilities:
- Intelligent routing to appropriate workers
- Parallel worker execution
- Multi-worker synthesis
- Hierarchical coordination (Level 2)

Usage:
    from src.agents.supervisors.news_supervisor import NewsSupervisor
    
    supervisor = NewsSupervisor()
    result = supervisor.process_query("What is the sentiment around tech stocks?")
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.messages import HumanMessage
from databricks_langchain import ChatDatabricks


class NewsSupervisor:
    """Level 2 supervisor coordinating News domain workers.
    
    Analyzes queries and routes to appropriate workers:
    - General news, timelines → GeneralNewsWorker
    - Sector news, competitive analysis → SectorNewsWorker
    - Market sentiment, investor mood → MarketSentimentWorker
    - Corporate events, earnings → EventDetectionWorker
    
    Executes workers in parallel and synthesizes results.
    """
    
    def __init__(self):
        """Initialize News Supervisor and workers."""
        self.llm = ChatDatabricks(
            endpoint="databricks-meta-llama-3-3-70b-instruct",
            temperature=0.1
        )
        
        # Initialize workers
        from src.agents.workers.general_news_worker import GeneralNewsWorker
        from src.agents.workers.sector_news_worker import SectorNewsWorker
        from src.agents.workers.market_sentiment_worker import MarketSentimentWorker
        from src.agents.workers.event_detection_worker import EventDetectionWorker
        
        self.workers = {
            'general': GeneralNewsWorker(),
            'sector': SectorNewsWorker(),
            'sentiment': MarketSentimentWorker(),
            'events': EventDetectionWorker()
        }
        
        print("✅ NewsSupervisor initialized with 4 workers")
    
    def process_query(
        self,
        query: str,
        days: int = 7,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """Process a news query by routing to appropriate workers.
        
        Args:
            query: User query about news, sentiment, events, or sectors
            days: Days to look back (default: 7)
            parallel: Execute workers in parallel (default: True)
        
        Returns:
            Dict with routing plan, worker results, and synthesis
        """
        print(f"\n🎯 NewsSupervisor processing query: {query}")
        print(f"   Days: {days} | Parallel: {parallel}")
        
        # Step 1: Routing - decide which workers to use
        routing = self._route_query(query, days)
        
        if not routing.get('success'):
            return {
                "success": False,
                "error": "Routing failed",
                "routing": routing,
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"\n📋 Routing Plan:")
        print(f"   Workers: {', '.join(routing['workers'])}")
        print(f"   Tasks: {len(routing['tasks'])}")
        
        # Step 2: Execute workers
        if parallel:
            results = self._execute_parallel(routing['tasks'])
        else:
            results = self._execute_sequential(routing['tasks'])
        
        # Step 3: Synthesize results
        synthesis = self._synthesize_results(query, routing, results)
        
        return {
            "success": True,
            "query": query,
            "days": days,
            "routing": routing,
            "worker_results": results,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat(),
            "supervisor": "NewsSupervisor"
        }
    
    def _route_query(self, query: str, days: int) -> Dict[str, Any]:
        """Use LLM to analyze query and decide which workers to invoke.
        
        Args:
            query: User query
            days: Days parameter
        
        Returns:
            Dict with workers list and tasks for each worker
        """
        routing_prompt = f"""
        Analyze this news/sentiment query and decide which workers to use:
        
        Query: {query}
        Timeframe: last {days} days
        
        Available workers and their methods:
        
        1. general (GeneralNewsWorker)
           Methods:
           - aggregate_news(query: str, days: int, categories: List[str]) - Aggregate news by topic
           - create_news_timeline(query: str, days: int) - Create chronological timeline
           Use for: broad news queries, timelines, general financial news
        
        2. sector (SectorNewsWorker)
           Methods:
           - analyze_sector_news(sector: str, days: int, include_competitors: bool) - Sector analysis
           - compare_sector_sentiment(sectors: List[str], days: int) - Compare multiple sectors
           - detect_sector_trends(sector: str, days: int) - Identify sector trends
           Use for: sector queries, competitive tracking, sector trends
           
        3. sentiment (MarketSentimentWorker)
           Methods:
           - analyze_sentiment(query: str, days_back: int) - Analyze market sentiment
           - track_sentiment_shift(query: str, days_back: int) - Track sentiment changes
           Use for: sentiment queries, market mood, investor outlook
        
        4. events (EventDetectionWorker)
           Methods:
           - detect_events(symbol: str, lookback_days: int, event_types: List[str]) - Detect corporate events
           - create_event_timeline(symbol: str, lookback_days: int) - Timeline of company events
           Use for: corporate events, earnings, M&A, IPOs, regulatory filings
        
        CRITICAL RULES:
        1. Use EXACT method names from above - do not invent method names
        2. Use EXACT parameter names - do not rename parameters:
           - sentiment methods use 'days_back' NOT 'days'
           - events methods use 'symbol' and 'lookback_days' NOT 'query' or 'days'
           - general/sector methods use 'days' (correct)
        3. If a method needs a stock symbol, use 'symbol' parameter
        4. Match the parameter names EXACTLY as shown in the method signatures
        
        Provide a routing plan in JSON format:
        {{
            "workers": ["general", "sector"],
            "tasks": [
                {{
                    "worker": "general",
                    "method": "aggregate_news",
                    "args": {{"query": "...", "days": {days}}},
                    "rationale": "why this worker"
                }},
                {{
                    "worker": "sentiment",
                    "method": "analyze_sentiment",
                    "args": {{"query": "...", "days_back": {days}}},
                    "rationale": "why this worker"
                }},
                {{
                    "worker": "events",
                    "method": "detect_events",
                    "args": {{"symbol": "TICKER", "lookback_days": {days}}},
                    "rationale": "why this worker"
                }}
            ],
            "reasoning": "overall routing strategy"
        }}
        
        Return ONLY the JSON, no other text.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=routing_prompt)])
            
            # Parse JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            routing = json.loads(content)
            routing['success'] = True
            return routing
            
        except Exception as e:
            print(f"⚠️  Routing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workers": [],
                "tasks": []
            }
    
    def _execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute worker tasks in parallel using ThreadPoolExecutor.
        
        Args:
            tasks: List of task dicts with worker, method, args
        
        Returns:
            List of worker results
        """
        print(f"\n⚡ Executing {len(tasks)} tasks in parallel...")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_task = {}
            
            for task in tasks:
                future = executor.submit(self._execute_task, task)
                future_to_task[future] = task
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    status = "✅" if result.get('success') else "❌"
                    print(f"   {status} {task['worker']}.{task['method']}")
                except Exception as e:
                    print(f"   ❌ {task['worker']}.{task['method']}: {str(e)}")
                    results.append({
                        "success": False,
                        "error": str(e),
                        "task": task
                    })
        
        return results
    
    def _execute_sequential(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute worker tasks sequentially.
        
        Args:
            tasks: List of task dicts
        
        Returns:
            List of worker results
        """
        print(f"\n🔄 Executing {len(tasks)} tasks sequentially...")
        
        results = []
        for task in tasks:
            result = self._execute_task(task)
            results.append(result)
            status = "✅" if result.get('success') else "❌"
            print(f"   {status} {task['worker']}.{task['method']}")
        
        return results
    
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single worker task.
        
        Args:
            task: Dict with worker, method, args
        
        Returns:
            Worker result dict
        """
        worker_name = task['worker']
        method_name = task['method']
        args = task.get('args', {})
        
        # Map common parameter names to worker-specific names
        if worker_name == 'sentiment' and 'days' in args:
            args['days_back'] = args.pop('days')
        elif worker_name == 'events':
            if 'days' in args:
                args['lookback_days'] = args.pop('days')
            if 'query' in args:
                # For events, use a default symbol or extract from query
                args['symbol'] = 'AAPL'
                args.pop('query')
        
        worker = self.workers.get(worker_name)
        if not worker:
            return {
                "success": False,
                "error": f"Worker {worker_name} not found",
                "task": task
            }
        
        method = getattr(worker, method_name, None)
        if not method:
            return {
                "success": False,
                "error": f"Method {method_name} not found on {worker_name}",
                "task": task
            }
        
        try:
            result = method(**args)
            result['task'] = task
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    def _synthesize_results(
        self,
        query: str,
        routing: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize worker results into a comprehensive answer.
        
        Args:
            query: Original query
            routing: Routing plan
            results: Worker results
        
        Returns:
            Synthesis dict with summary and insights
        """
        print(f"\n🔬 Synthesizing {len(results)} worker results...")
        
        # Build synthesis prompt
        results_summary = []
        for i, result in enumerate(results, 1):
            task = result.get('task', {})
            worker = task.get('worker', 'unknown')
            method = task.get('method', 'unknown')
            
            if result.get('success'):
                # Extract key content from result
                content = result.get('analysis') or result.get('sentiment') or result.get('events') or result.get('timeline') or str(result)
                results_summary.append(f"Worker {i} ({worker}.{method}):\n{content[:500]}...")
            else:
                results_summary.append(f"Worker {i} ({worker}.{method}): FAILED - {result.get('error', 'unknown')}")
        
        synthesis_prompt = f"""
        Synthesize these news worker results into a comprehensive answer.
        
        Original Query: {query}
        
        Worker Results:
        {chr(10).join(results_summary)}
        
        Provide:
        1. Executive Summary (2-3 sentences answering the query)
        2. Key Insights (3-5 bullet points from worker results)
        3. News Highlights (important developments or events)
        4. Sentiment Assessment (if applicable)
        5. Investment Implications (if applicable)
        
        Be concise, actionable, and data-driven.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=synthesis_prompt)])
            
            return {
                "success": True,
                "summary": response.content,
                "workers_used": len(results),
                "workers_succeeded": sum(1 for r in results if r.get('success')),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"⚠️  Synthesis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workers_used": len(results),
                "timestamp": datetime.now().isoformat()
            }
