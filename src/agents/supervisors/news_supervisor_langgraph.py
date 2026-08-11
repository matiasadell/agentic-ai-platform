"""NewsSupervisor implemented with LangGraph.

This is a declarative alternative to news_supervisor.py (which uses
ThreadPoolExecutor + LLM-based routing) for:
- Automatic parallel worker execution
- Declarative routing
- Built-in state management
- Graceful degradation
- Visualization support

Coordinates the same 4 workers as news_supervisor.py:
- MarketSentimentWorker: market sentiment analysis
- GeneralNewsWorker: batch news ingestion, filtering, categorization
- SectorNewsWorker: sector-specific analysis, sentiment, trends
- EventDetectionWorker: corporate events (earnings, M&A, IPOs)

Architecture:
    START → router → [sentiment, news, sector, event] → synthesis → END
                     (parallel execution, automatic merge)

Note (2026-08-11): this file previously imported from a nonexistent
`src.workers.news` module with worker class names (NewsAnalysisWorker,
CorporateEventWorker) that never matched any class in this repo - it
could not be imported. Rewritten to use the real worker classes in
`src.agents.workers.*` and their real method signatures (see
news_supervisor.py's routing prompt, which documents these signatures
precisely: sentiment methods use 'days_back', event methods use 'symbol'
and 'lookback_days', general/sector methods use 'days').
"""

from typing import Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from src.agents.state import NewsSupervisorState
from src.agents.workers.market_sentiment_worker import MarketSentimentWorker
from src.agents.workers.general_news_worker import GeneralNewsWorker
from src.agents.workers.sector_news_worker import SectorNewsWorker
from src.agents.workers.event_detection_worker import EventDetectionWorker


# ============================================================================
# NODE DEFINITIONS
# ============================================================================

def router_node(state: NewsSupervisorState) -> dict[str, Any]:
    """Route query to appropriate news workers.

    Returns next_nodes for parallel execution.
    """
    query = state["query"].lower()
    workers = []

    # Rule-based routing
    if any(kw in query for kw in ["sentiment", "feeling", "mood", "bullish", "bearish"]):
        workers.append("sentiment_worker")

    if any(kw in query for kw in ["news", "article", "headline", "media", "report"]):
        workers.append("news_worker")

    if any(kw in query for kw in ["sector", "industry", "tech", "finance", "healthcare", "energy"]):
        workers.append("sector_worker")

    if any(kw in query for kw in ["earnings", "merger", "acquisition", "dividend", "event", "m&a", "ipo"]):
        workers.append("event_worker")

    # Fallback: run sentiment + news
    if not workers:
        workers = ["sentiment_worker", "news_worker"]

    return {
        "selected_workers": workers,
        "next_nodes": workers,
    }


def sentiment_worker_node(state: NewsSupervisorState) -> dict[str, Any]:
    """Execute MarketSentimentWorker."""
    query = state["query"]
    days = state.get("days", 7)

    try:
        worker = MarketSentimentWorker()
        result = worker.analyze_sentiment(query=query, days_back=days)

        return {
            "worker_results": [{
                "success": True,
                "worker_name": "MarketSentimentWorker",
                "query": query,
                "summary": result.get("summary", str(result)) if isinstance(result, dict) else str(result),
                "sentiment_score": result.get("sentiment_score") if isinstance(result, dict) else None,
                "raw": result,
            }]
        }

    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "MarketSentimentWorker",
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            }]
        }


def news_worker_node(state: NewsSupervisorState) -> dict[str, Any]:
    """Execute GeneralNewsWorker."""
    query = state["query"]
    days = state.get("days", 7)

    try:
        worker = GeneralNewsWorker()
        result = worker.aggregate_news(query=query, days=days)

        return {
            "worker_results": [{
                "success": True,
                "worker_name": "GeneralNewsWorker",
                "query": query,
                "summary": result.get("summary", str(result)) if isinstance(result, dict) else str(result),
                "articles_analyzed": result.get("articles_analyzed") if isinstance(result, dict) else None,
                "raw": result,
            }]
        }

    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "GeneralNewsWorker",
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            }]
        }


def sector_worker_node(state: NewsSupervisorState) -> dict[str, Any]:
    """Execute SectorNewsWorker."""
    query = state["query"]
    days = state.get("days", 7)

    try:
        worker = SectorNewsWorker()

        # Auto-detect sector from query (naive keyword match)
        sector = "technology"  # Default
        if "finance" in query.lower():
            sector = "finance"
        elif "healthcare" in query.lower():
            sector = "healthcare"
        elif "energy" in query.lower():
            sector = "energy"

        result = worker.analyze_sector_news(sector=sector, days=days)

        return {
            "worker_results": [{
                "success": True,
                "worker_name": "SectorNewsWorker",
                "query": query,
                "summary": result.get("summary", str(result)) if isinstance(result, dict) else str(result),
                "raw": result,
            }]
        }

    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "SectorNewsWorker",
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            }]
        }


def event_worker_node(state: NewsSupervisorState) -> dict[str, Any]:
    """Execute EventDetectionWorker.

    detect_events() requires a stock ticker symbol, not a free-text
    query (see news_supervisor.py's routing prompt). Since this graph
    only has a free-text query at this point, ticker extraction is not
    implemented - the raw query is passed through as-is, same
    limitation macro_supervisor_langgraph.py has for ticker/country
    parameters. A real implementation would need an upstream step (LLM
    or regex) to extract a ticker before reaching this node.
    """
    query = state["query"]
    days = state.get("days", 7)

    try:
        worker = EventDetectionWorker()
        result = worker.detect_events(symbol=query, lookback_days=days)

        return {
            "worker_results": [{
                "success": True,
                "worker_name": "EventDetectionWorker",
                "query": query,
                "summary": result.get("summary", str(result)) if isinstance(result, dict) else str(result),
                "raw": result,
            }]
        }

    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "EventDetectionWorker",
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            }]
        }


def synthesis_node(state: NewsSupervisorState) -> dict[str, Any]:
    """Synthesize all worker results.

    LangGraph auto-merged worker_results via Annotated[list, operator.add].
    """
    worker_results = state.get("worker_results", [])
    query = state["query"]
    days = state.get("days", 7)

    # Separate successful/failed
    successful = [r for r in worker_results if r.get("success", False)]
    failed = [r for r in worker_results if not r.get("success", False)]

    # Build synthesis
    synthesis_parts = [
        f"# NewsSupervisor Analysis: {query}",
        f"\nTime period: Last {days} days",
        f"\nWorkers executed: {len(worker_results)}",
        f"  Successful: {len(successful)}",
        f"  Failed: {len(failed)}",
        "",
    ]

    # Extract key metrics
    sentiment_scores = []
    total_articles = 0

    for result in successful:
        worker_name = result.get("worker_name", "Unknown")

        # Collect sentiment scores
        if result.get("sentiment_score") is not None:
            sentiment_scores.append(result["sentiment_score"])

        # Collect article counts
        if result.get("articles_analyzed"):
            total_articles += result.get("articles_analyzed", 0)

        # Add summary
        summary = result.get("summary", "No summary")
        synthesis_parts.append(f"\n### {worker_name}")
        synthesis_parts.append(str(summary)[:400])

    # Add aggregate metrics
    if sentiment_scores:
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        synthesis_parts.insert(5, f"\nAverage Sentiment: {avg_sentiment:.2f}/10")

    if total_articles > 0:
        synthesis_parts.insert(6, f"Total Articles Analyzed: {total_articles}")

    # Graceful degradation message
    if failed:
        synthesis_parts.append("\n## Partial Results (Some Workers Failed):")
        for result in failed:
            worker_name = result.get("worker_name", "Unknown")
            error_type = result.get("error_type", "Unknown")
            synthesis_parts.append(f"  - {worker_name}: {error_type}")
        synthesis_parts.append("\nAnalysis continues with available data.")

    synthesis = "\n".join(synthesis_parts)

    return {"synthesis": synthesis}


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_after_router(state: NewsSupervisorState) -> list[str]:
    """Return worker nodes for parallel execution."""
    return state.get("next_nodes", [])


# ============================================================================
# BUILD GRAPH
# ============================================================================

def create_news_supervisor_graph() -> StateGraph:
    """Create NewsSupervisor StateGraph.

    Returns:
        Compiled graph ready for invocation
    """
    graph = StateGraph(NewsSupervisorState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("sentiment_worker", sentiment_worker_node)
    graph.add_node("news_worker", news_worker_node)
    graph.add_node("sector_worker", sector_worker_node)
    graph.add_node("event_worker", event_worker_node)
    graph.add_node("synthesis", synthesis_node)

    # Define edges
    graph.set_entry_point("router")

    # Conditional parallel routing
    graph.add_conditional_edges(
        "router",
        route_after_router,
        ["sentiment_worker", "news_worker", "sector_worker", "event_worker"]
    )

    # All workers → synthesis
    graph.add_edge("sentiment_worker", "synthesis")
    graph.add_edge("news_worker", "synthesis")
    graph.add_edge("sector_worker", "synthesis")
    graph.add_edge("event_worker", "synthesis")

    # Synthesis → END
    graph.add_edge("synthesis", END)

    return graph.compile()


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

news_supervisor_app = create_news_supervisor_graph()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example 1: Basic invocation
    result = news_supervisor_app.invoke({
        "query": "Tesla stock sentiment",
        "days": 7
    })
    print(result["synthesis"])

    # Example 2: With custom config
    config = RunnableConfig(run_name="news_analysis")
    result = news_supervisor_app.invoke(
        {"query": "Tech sector news and M&A activity", "days": 14},
        config=config
    )
    print(result["synthesis"])

    # Example 3: Visualization
    from IPython.display import Image, display
    display(Image(news_supervisor_app.get_graph().draw_mermaid_png()))
