"""LangGraph State Definitions for Supervisors.

Define TypedDict states for each supervisor to enable:
- Automatic state management by LangGraph
- Pydantic validation
- Type safety
- Automatic merge of worker results with Annotated + operator.add
"""

from typing import TypedDict, Annotated, Sequence, Optional, Any
import operator


# ============================================================================
# MACRO SUPERVISOR STATE
# ============================================================================

class MacroSupervisorState(TypedDict, total=False):
    """State for MacroSupervisor.
    
    LangGraph automatically manages this state across all nodes.
    Use Annotated[list, operator.add] for automatic merging of worker results.
    
    Attributes:
        query: Original user query
        selected_workers: List of worker names to execute (from router)
        worker_results: Accumulated results from all workers (auto-merged)
        synthesis: Final synthesized response
        next_nodes: Node names for conditional routing
        error: Error message if supervisor fails
    """
    query: str
    selected_workers: list[str]
    worker_results: Annotated[list[dict[str, Any]], operator.add]  # Auto-merge
    synthesis: str
    next_nodes: list[str]  # For conditional_edges
    error: Optional[str]


# ============================================================================
# NEWS SUPERVISOR STATE
# ============================================================================

class NewsSupervisorState(TypedDict, total=False):
    """State for NewsSupervisor.
    
    LangGraph automatically manages this state across all nodes.
    
    Attributes:
        query: Original user query
        days: Lookback period in days
        selected_workers: List of worker names to execute (from router)
        worker_results: Accumulated results from all workers (auto-merged)
        synthesis: Final synthesized response
        next_nodes: Node names for conditional routing
        error: Error message if supervisor fails
    """
    query: str
    days: int
    selected_workers: list[str]
    worker_results: Annotated[list[dict[str, Any]], operator.add]  # Auto-merge
    synthesis: str
    next_nodes: list[str]  # For conditional_edges
    error: Optional[str]




# ============================================================================
# FUNDAMENTAL SUPERVISOR STATE
# ============================================================================

class FundamentalSupervisorState(TypedDict, total=False):
    """State for FundamentalSupervisor.
    
    LangGraph automatically manages this state across all nodes.
    
    Attributes:
        query: Original user query
        ticker: Stock ticker symbol (e.g., "TSLA", "AAPL")
        selected_workers: List of worker names to execute (from router)
        worker_results: Accumulated results from all workers (auto-merged)
        synthesis: Final synthesized response
        next_nodes: Node names for conditional routing
        error: Error message if supervisor fails
    """
    query: str
    ticker: str
    selected_workers: list[str]
    worker_results: Annotated[list[dict[str, Any]], operator.add]  # Auto-merge
    synthesis: str
    next_nodes: list[str]  # For conditional_edges
    error: Optional[str]


# ============================================================================
# HELPER: State with Messages (for future LLM-based routing)
# ============================================================================

from langchain_core.messages import BaseMessage

class SupervisorStateWithMessages(TypedDict, total=False):
    """State with LangChain messages for LLM-based routing.
    
    Use this when routing logic needs conversational context.
    For now, we use simple rule-based routing, but this enables
    future LLM-based routing with memory.
    
    Attributes:
        messages: Conversational history for LLM routing
        query: Original user query
        selected_workers: List of worker names
        worker_results: Accumulated worker results
        synthesis: Final response
        next_nodes: For conditional routing
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    selected_workers: list[str]
    worker_results: Annotated[list[dict[str, Any]], operator.add]
    synthesis: str
    next_nodes: list[str]
