"""FundamentalSupervisor implemented with LangGraph.

Complete LangGraph implementation for fundamental analysis:
- Automatic parallel worker execution
- Declarative routing
- Built-in state management
- Graceful degradation
- Visualization support

Architecture:
    START → router → [financial, ratios, earnings, valuation] → synthesis → END
                     (parallel execution, automatic merge)
"""

from typing import Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from src.agents.state import FundamentalSupervisorState
from src.workers.fundamental import (
    FinancialStatementWorker,
    KeyRatiosWorker,
    EarningsWorker,
    ValuationWorker
)


# ============================================================================
# NODE DEFINITIONS
# ============================================================================

def router_node(state: FundamentalSupervisorState) -> dict[str, Any]:
    """Route query to appropriate fundamental workers.
    
    Returns next_nodes for parallel execution.
    """
    query = state["query"].lower()
    workers = []
    
    # Rule-based routing
    if any(kw in query for kw in ["balance", "asset", "liability", "equity", "financial statement", "income", "cash flow"]):
        workers.append("financial_worker")
    
    if any(kw in query for kw in ["ratio", "p/e", "roe", "roa", "margin", "liquidity", "profitability"]):
        workers.append("ratios_worker")
    
    if any(kw in query for kw in ["earnings", "eps", "revenue", "guidance", "beat", "miss", "analyst"]):
        workers.append("earnings_worker")
    
    if any(kw in query for kw in ["valuation", "dcf", "intrinsic", "fair value", "overvalued", "undervalued", "worth"]):
        workers.append("valuation_worker")
    
    # Fallback: if no specific match, run all workers (comprehensive analysis)
    if not workers:
        workers = ["financial_worker", "ratios_worker", "earnings_worker", "valuation_worker"]
    
    return {
        "selected_workers": workers,
        "next_nodes": workers
    }


def financial_worker_node(state: FundamentalSupervisorState) -> dict[str, Any]:
    """Execute FinancialStatementWorker."""
    query = state["query"]
    ticker = state.get("ticker", "UNKNOWN")
    
    try:
        worker = FinancialStatementWorker()
        result = worker.analyze_statements(
            ticker=ticker,
            query=query,
            period="latest",
            statements=["balance", "income", "cashflow"]
        )
        
        return {"worker_results": [result]}
        
    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "FinancialStatementWorker",
                "query": query,
                "ticker": ticker,
                "error": str(e),
                "error_type": type(e).__name__
            }]
        }


def ratios_worker_node(state: FundamentalSupervisorState) -> dict[str, Any]:
    """Execute KeyRatiosWorker."""
    query = state["query"]
    ticker = state.get("ticker", "UNKNOWN")
    
    try:
        worker = KeyRatiosWorker()
        result = worker.calculate_ratios(
            ticker=ticker,
            query=query,
            ratio_categories=["valuation", "profitability", "liquidity", "efficiency"]
        )
        
        return {"worker_results": [result]}
        
    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "KeyRatiosWorker",
                "query": query,
                "ticker": ticker,
                "error": str(e),
                "error_type": type(e).__name__
            }]
        }


def earnings_worker_node(state: FundamentalSupervisorState) -> dict[str, Any]:
    """Execute EarningsWorker."""
    query = state["query"]
    ticker = state.get("ticker", "UNKNOWN")
    
    try:
        worker = EarningsWorker()
        result = worker.analyze_earnings(
            ticker=ticker,
            query=query,
            quarters=1
        )
        
        return {"worker_results": [result]}
        
    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "EarningsWorker",
                "query": query,
                "ticker": ticker,
                "error": str(e),
                "error_type": type(e).__name__
            }]
        }


def valuation_worker_node(state: FundamentalSupervisorState) -> dict[str, Any]:
    """Execute ValuationWorker."""
    query = state["query"]
    ticker = state.get("ticker", "UNKNOWN")
    
    try:
        worker = ValuationWorker()
        result = worker.estimate_value(
            ticker=ticker,
            query=query,
            methods=["dcf", "comparables"]
        )
        
        return {"worker_results": [result]}
        
    except Exception as e:
        return {
            "worker_results": [{
                "success": False,
                "worker_name": "ValuationWorker",
                "query": query,
                "ticker": ticker,
                "error": str(e),
                "error_type": type(e).__name__
            }]
        }


def synthesis_node(state: FundamentalSupervisorState) -> dict[str, Any]:
    """Synthesize all worker results into final fundamental analysis.
    
    LangGraph auto-merged worker_results via Annotated[list, operator.add].
    """
    worker_results = state.get("worker_results", [])
    query = state["query"]
    ticker = state.get("ticker", "UNKNOWN")
    
    # Separate successful/failed
    successful = [r for r in worker_results if r.get("success", False)]
    failed = [r for r in worker_results if not r.get("success", False)]
    
    # Build synthesis
    synthesis_parts = [
        f"# Fundamental Analysis: {ticker}",
        f"\nQuery: {query}",
        f"\nWorkers executed: {len(worker_results)}",
        f"  ✅ Successful: {len(successful)}",
        f"  ❌ Failed: {len(failed)}",
        ""
    ]
    
    # Extract key metrics from each worker
    for result in successful:
        worker_name = result.get("worker_name", "Unknown")
        summary = result.get("summary", "No summary available")
        
        synthesis_parts.append(f"\n### {worker_name}")
        
        # Add worker-specific highlights
        if worker_name == "FinancialStatementWorker":
            if "revenue" in result and result["revenue"] is not None:
                synthesis_parts.append(f"  • Revenue: ${result['revenue']:,.0f}")
            if "net_income" in result and result["net_income"] is not None:
                synthesis_parts.append(f"  • Net Income: ${result['net_income']:,.0f}")
            if "free_cash_flow" in result and result["free_cash_flow"] is not None:
                synthesis_parts.append(f"  • Free Cash Flow: ${result['free_cash_flow']:,.0f}")
        
        elif worker_name == "KeyRatiosWorker":
            if "pe_ratio" in result and result["pe_ratio"]:
                synthesis_parts.append(f"  • P/E Ratio: {result['pe_ratio']}")
            if "roe" in result and result["roe"]:
                synthesis_parts.append(f"  • ROE: {result['roe']}%")
            if "current_ratio" in result and result["current_ratio"]:
                synthesis_parts.append(f"  • Current Ratio: {result['current_ratio']}")
        
        elif worker_name == "EarningsWorker":
            if "eps_surprise_percent" in result and result["eps_surprise_percent"]:
                beat_miss = "Beat" if result["eps_surprise_percent"] > 0 else "Missed"
                synthesis_parts.append(f"  • {beat_miss} EPS by {abs(result['eps_surprise_percent']):.1f}%")
            if "guidance_raised" in result:
                guidance_text = "raised" if result["guidance_raised"] else "maintained/lowered"
                synthesis_parts.append(f"  • Guidance: {guidance_text}")
        
        elif worker_name == "ValuationWorker":
            if "fair_value_estimate" in result and result["fair_value_estimate"]:
                synthesis_parts.append(f"  • Fair Value: ${result['fair_value_estimate']:.2f}")
            if "upside_downside" in result and result["upside_downside"]:
                updown = "upside" if result["upside_downside"] > 0 else "downside"
                synthesis_parts.append(f"  • {abs(result['upside_downside']):.1f}% {updown}")
            if "valuation_rating" in result:
                synthesis_parts.append(f"  • Rating: {result['valuation_rating']}")
        
        # Add summary (truncated)
        synthesis_parts.append(f"\n{summary[:300]}...")
    
    # Graceful degradation message
    if failed:
        synthesis_parts.append("\n## ⚠️ Partial Results (Some Workers Failed):")
        for result in failed:
            worker_name = result.get("worker_name", "Unknown")
            error_type = result.get("error_type", "Unknown")
            synthesis_parts.append(f"  - {worker_name}: {error_type}")
        synthesis_parts.append("\n💡 Analysis continues with available data.")
    
    synthesis = "\n".join(synthesis_parts)
    
    return {"synthesis": synthesis}


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_after_router(state: FundamentalSupervisorState) -> list[str]:
    """Return worker nodes for parallel execution."""
    return state.get("next_nodes", [])


# ============================================================================
# BUILD GRAPH
# ============================================================================

def create_fundamental_supervisor_graph() -> StateGraph:
    """Create FundamentalSupervisor StateGraph.
    
    Returns:
        Compiled graph ready for invocation
    """
    graph = StateGraph(FundamentalSupervisorState)
    
    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("financial_worker", financial_worker_node)
    graph.add_node("ratios_worker", ratios_worker_node)
    graph.add_node("earnings_worker", earnings_worker_node)
    graph.add_node("valuation_worker", valuation_worker_node)
    graph.add_node("synthesis", synthesis_node)
    
    # Define edges
    graph.set_entry_point("router")
    
    # Conditional parallel routing
    graph.add_conditional_edges(
        "router",
        route_after_router,
        ["financial_worker", "ratios_worker", "earnings_worker", "valuation_worker"]
    )
    
    # All workers → synthesis
    graph.add_edge("financial_worker", "synthesis")
    graph.add_edge("ratios_worker", "synthesis")
    graph.add_edge("earnings_worker", "synthesis")
    graph.add_edge("valuation_worker", "synthesis")
    
    # Synthesis → END
    graph.add_edge("synthesis", END)
    
    return graph.compile()


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

fundamental_supervisor_app = create_fundamental_supervisor_graph()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example 1: Basic invocation
    result = fundamental_supervisor_app.invoke({
        "query": "Analyze Tesla financials and valuation",
        "ticker": "TSLA"
    })
    print(result["synthesis"])
    
    # Example 2: With custom config
    config = RunnableConfig(run_name="fundamental_analysis")
    result = fundamental_supervisor_app.invoke(
        {"query": "Is Apple undervalued? Check P/E and earnings", "ticker": "AAPL"},
        config=config
    )
    print(result["synthesis"])
    
    # Example 3: Visualization
    from IPython.display import Image, display
    display(Image(fundamental_supervisor_app.get_graph().draw_mermaid_png()))
