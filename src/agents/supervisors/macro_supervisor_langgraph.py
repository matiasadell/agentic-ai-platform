"""MacroSupervisor implemented with LangGraph.

This is a declarative alternative to macro_supervisor.py (which uses
ThreadPoolExecutor + LLM-based routing) for:
- Automatic parallelism (no ThreadPoolExecutor needed)
- Declarative routing with conditional_edges
- Built-in state management and validation
- Automatic visualization with Mermaid
- Less orchestration code than the manual implementation

Coordinates the same 3 workers as macro_supervisor.py:
- MacroDataWorker: GDP, inflation, unemployment, interest rates
- RegionalContextWorker: regional economic context and news
- IndicatorAnalysisWorker: stock prices and technical indicators

Architecture:
    START → router → [macro, regional, indicator] → synthesis → END
                     (parallel execution, automatic merge)

Note (2026-08-11): this file previously imported from a nonexistent
`src.workers.macro` module with worker class names (RegionalDataWorker,
TechnicalIndicatorWorker, EconomicEventWorker) that never matched any
class in this repo — it could not be imported. Rewritten to use the real
worker classes in `src.agents.workers.*`. There is no macro-economic
"event" worker in this codebase (EventDetectionWorker exists but is a
News-domain worker for corporate events, not FOMC/Fed-style macro
events), so the event_worker node from the original design was dropped
rather than faked.
"""

from typing import Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from src.agents.state import MacroSupervisorState
from src.agents.workers.macro_data_worker import MacroDataWorker
from src.agents.workers.regional_context_worker import RegionalContextWorker
from src.agents.workers.indicator_analysis_worker import IndicatorAnalysisWorker


# ============================================================================
# NODE DEFINITIONS (Simple functions - LangGraph handles the rest)
# ============================================================================

def router_node(state: MacroSupervisorState) -> dict[str, Any]:
    """Route query to appropriate workers.

    Returns next_nodes list for conditional_edges routing.
    LangGraph will execute all listed nodes in parallel automatically.
    """
    query = state["query"].lower()
    workers = []

    # Rule-based routing (can be replaced with LLM later, as macro_supervisor.py does)
    if any(kw in query for kw in ["gdp", "inflation", "unemployment", "interest rate", "macro", "economic data"]):
        workers.append("macro_worker")

    if any(kw in query for kw in ["region", "country", "policy", "context", "latin america", "asia", "europe"]):
        workers.append("regional_worker")

    if any(kw in query for kw in ["stock", "ticker", "rsi", "macd", "sma", "ema", "technical", "indicator", "price"]):
        workers.append("indicator_worker")

    # Fallback: if no specific match, run macro + regional
    if not workers:
        workers = ["macro_worker", "regional_worker"]

    return {
        "selected_workers": workers,
        "next_nodes": workers,  # For conditional_edges
    }


def macro_worker_node(state: MacroSupervisorState) -> dict[str, Any]:
    """Execute MacroDataWorker."""
    query = state["query"]

    try:
        worker = MacroDataWorker()
        # analyze_economy() expects a country/region name. As in
        # macro_supervisor.py, we pass the raw query through - routing
        # to a specific country is not yet implemented.
        result = worker.analyze_economy(query)

        return {
            "worker_results": [{
                "success": result.get("success", True),
                "worker_name": "MacroDataWorker",
                "query": query,
                "summary": result.get("summary", str(result)),
                "raw": result,
            }]
        }

    except Exception as e:
        # Graceful degradation: return error response
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "MacroDataWorker",
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            }]
        }


def regional_worker_node(state: MacroSupervisorState) -> dict[str, Any]:
    """Execute RegionalContextWorker."""
    query = state["query"]

    try:
        worker = RegionalContextWorker()
        result = worker.analyze_region(query=query)

        return {
            "worker_results": [{
                "success": True,
                "worker_name": "RegionalContextWorker",
                "query": query,
                "summary": result.get("analysis", str(result)),
                "raw": result,
            }]
        }

    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "RegionalContextWorker",
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            }]
        }


def indicator_worker_node(state: MacroSupervisorState) -> dict[str, Any]:
    """Execute IndicatorAnalysisWorker."""
    query = state["query"]

    try:
        worker = IndicatorAnalysisWorker()
        # analyze_stock() expects a ticker symbol. As in
        # macro_supervisor.py, we pass the raw query through - extracting
        # a ticker from free text is not yet implemented.
        result = worker.analyze_stock(query)

        return {
            "worker_results": [{
                "success": True,
                "worker_name": "IndicatorAnalysisWorker",
                "query": query,
                "summary": result.get("analysis", str(result)),
                "raw": result,
            }]
        }

    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "IndicatorAnalysisWorker",
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            }]
        }


def synthesis_node(state: MacroSupervisorState) -> dict[str, Any]:
    """Synthesize all worker results into final response.

    LangGraph has already merged all worker_results via Annotated[list, operator.add].
    We just need to format the final output.
    """
    worker_results = state.get("worker_results", [])
    query = state["query"]

    # Separate successful and failed workers
    successful = [r for r in worker_results if r.get("success", False)]
    failed = [r for r in worker_results if not r.get("success", False)]

    # Build synthesis
    synthesis_parts = [
        f"# MacroSupervisor Analysis: {query}",
        f"\nExecuted {len(worker_results)} workers:",
        f"  Successful: {len(successful)}",
        f"  Failed: {len(failed)}",
        "",
    ]

    # Add successful worker summaries
    if successful:
        synthesis_parts.append("## Successful Analyses:")
        for result in successful:
            worker_name = result.get("worker_name", "Unknown")
            summary = result.get("summary", "No summary available")
            synthesis_parts.append(f"\n### {worker_name}")
            synthesis_parts.append(str(summary)[:500])  # Truncate for readability

    # Add failed worker info (graceful degradation)
    if failed:
        synthesis_parts.append("\n## Failed Workers (Partial Results):")
        for result in failed:
            worker_name = result.get("worker_name", "Unknown")
            error_type = result.get("error_type", "Unknown")
            synthesis_parts.append(f"  - {worker_name}: {error_type}")

    synthesis = "\n".join(synthesis_parts)

    return {"synthesis": synthesis}


# ============================================================================
# CONDITIONAL ROUTING LOGIC
# ============================================================================

def route_after_router(state: MacroSupervisorState) -> list[str]:
    """Return list of worker nodes to execute in parallel.

    LangGraph will execute all returned nodes in parallel automatically.
    """
    return state.get("next_nodes", [])


def should_synthesize(state: MacroSupervisorState) -> Literal["synthesis", END]:
    """Always go to synthesis after workers complete."""
    return "synthesis"


# ============================================================================
# BUILD GRAPH
# ============================================================================

def create_macro_supervisor_graph() -> StateGraph:
    """Create MacroSupervisor StateGraph.

    Returns:
        Compiled graph ready for invocation
    """
    # Initialize graph with state schema
    graph = StateGraph(MacroSupervisorState)

    # Add nodes (order doesn't matter - LangGraph figures it out)
    graph.add_node("router", router_node)
    graph.add_node("macro_worker", macro_worker_node)
    graph.add_node("regional_worker", regional_worker_node)
    graph.add_node("indicator_worker", indicator_worker_node)
    graph.add_node("synthesis", synthesis_node)

    # Define edges
    graph.set_entry_point("router")

    # Conditional routing from router to workers (parallel execution)
    graph.add_conditional_edges(
        "router",
        route_after_router,  # Returns list of worker nodes
        ["macro_worker", "regional_worker", "indicator_worker"]
    )

    # All workers → synthesis (LangGraph waits for all parallel nodes)
    graph.add_edge("macro_worker", "synthesis")
    graph.add_edge("regional_worker", "synthesis")
    graph.add_edge("indicator_worker", "synthesis")

    # Synthesis → END
    graph.add_edge("synthesis", END)

    return graph.compile()


# ============================================================================
# CONVENIENCE: Create singleton instance
# ============================================================================

macro_supervisor_app = create_macro_supervisor_graph()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example 1: Simple invocation
    result = macro_supervisor_app.invoke({"query": "What's the current GDP growth rate?"})
    print(result["synthesis"])

    # Example 2: With config (for tracing, callbacks, etc.)
    config = RunnableConfig(run_name="macro_analysis_session")
    result = macro_supervisor_app.invoke(
        {"query": "Analyze US inflation and Fed policy"},
        config=config
    )
    print(result["synthesis"])

    # Example 3: Visualization
    from IPython.display import Image, display
    display(Image(macro_supervisor_app.get_graph().draw_mermaid_png()))
