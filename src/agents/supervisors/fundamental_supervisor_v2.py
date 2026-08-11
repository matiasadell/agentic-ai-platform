"""Fundamental Supervisor with Multi-Agent Coordination (LangGraph).

True hierarchical multi-agent architecture:
- Supervisor coordinates multiple ReAct agents  
- Each agent has its own LLM and can reason
- Uses LangGraph StateGraph for orchestration
- Follows pattern from 8-multiagent notebook

Architecture:
    START → financial_agent → ratios_agent → earnings_agent → valuation_agent → END
    (Sequential execution, all agents contribute to analysis)
"""

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, END, START
from src.agents.fundamental_agents import (
    create_financial_statement_agent,
    create_key_ratios_agent,
    create_earnings_agent,
    create_valuation_agent
)


def create_fundamental_supervisor(llm=None):
    """Create fundamental analysis supervisor with multi-agent coordination.
    
    The supervisor executes all 4 agents sequentially:
    1. financial_statement_agent - Analyzes financial statements
    2. key_ratios_agent - Calculates key ratios
    3. earnings_agent - Analyzes earnings data
    4. valuation_agent - Estimates valuation
    
    Returns:
        Compiled LangGraph application
    """
    if llm is None:
        llm = init_chat_model("openai:gpt-4o-mini")
    
    # Create all fundamental agents
    financial_agent = create_financial_statement_agent(llm)
    ratios_agent = create_key_ratios_agent(llm)
    earnings_agent = create_earnings_agent(llm)
    valuation_agent = create_valuation_agent(llm)
    
    # Define agent nodes
    def financial_agent_node(state: MessagesState):
        result = financial_agent.invoke(state)
        return {"messages": result["messages"]}
    
    def ratios_agent_node(state: MessagesState):
        result = ratios_agent.invoke(state)
        return {"messages": result["messages"]}
    
    def earnings_agent_node(state: MessagesState):
        result = earnings_agent.invoke(state)
        return {"messages": result["messages"]}
    
    def valuation_agent_node(state: MessagesState):
        result = valuation_agent.invoke(state)
        return {"messages": result["messages"]}
    
    # Build graph
    workflow = StateGraph(MessagesState)
    
    # Add nodes
    workflow.add_node("financial_agent", financial_agent_node)
    workflow.add_node("ratios_agent", ratios_agent_node)
    workflow.add_node("earnings_agent", earnings_agent_node)
    workflow.add_node("valuation_agent", valuation_agent_node)
    
    # Sequential execution: all agents run in order
    workflow.add_edge(START, "financial_agent")
    workflow.add_edge("financial_agent", "ratios_agent")
    workflow.add_edge("ratios_agent", "earnings_agent")
    workflow.add_edge("earnings_agent", "valuation_agent")
    workflow.add_edge("valuation_agent", END)
    
    return workflow.compile()


# Create singleton instance (lazy init to avoid API key issues at import)
_supervisor = None

def get_fundamental_supervisor():
    """Get or create the fundamental supervisor instance."""
    global _supervisor
    if _supervisor is None:
        _supervisor = create_fundamental_supervisor()
    return _supervisor


__all__ = [
    'create_fundamental_supervisor',
    'get_fundamental_supervisor'
]
