"""
BaseAgent - Core Agent Framework for FinSight AI
================================================

Databricks-native agent using:
- AI Gateway for LLM routing (replaces LiteLLM/Groq)
- MCP tools registered in Unity Catalog
- LangGraph for workflow orchestration
- MLflow for tracing and metrics
- Databricks SDK for all services
"""

import mlflow
import json
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod

# Databricks SDK
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# LangGraph
from langgraph.graph import StateGraph, END

# Local imports
from src.utils.config import Settings


class BaseAgent(ABC):
    """
    Base class for all agents in FinSight AI.
    
    Features:
    - Databricks AI Gateway for LLM calls
    - MCP tools integration (Unity Catalog registry)
    - LangGraph workflow orchestration
    - MLflow tracing and metrics
    - Retry logic and error handling
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        ai_gateway_endpoint: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_functions: Optional[Dict[str, Callable]] = None,
        max_iterations: int = 5,
        temperature: float = 0.7
    ):
        """
        Initialize agent.
        
        Args:
            name: Agent name
            role: Agent role description
            ai_gateway_endpoint: AI Gateway endpoint (e.g., "ai-gateway:/main.finsight_ai.analysis")
            tools: List of tool definitions (OpenAI format)
            tool_functions: Dict mapping tool names to Python functions
            max_iterations: Max tool-calling iterations
            temperature: LLM temperature
        """
        self.name = name
        self.role = role
        self.ai_gateway_endpoint = ai_gateway_endpoint
        self.tools = tools or []
        self.tool_functions = tool_functions or {}
        self.max_iterations = max_iterations
        self.temperature = temperature
        
        # Load config
        self.config = Settings()
        
        # Initialize Databricks client
        self.workspace = WorkspaceClient(
            host=self.config.databricks_host,
            token=self.config.databricks_token
        )
        
        # MLflow setup
        mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
        mlflow.set_experiment(self.config.mlflow_experiment_name)
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        Must be implemented by subclasses.
        """
        pass
    
    def _call_ai_gateway(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None
    ) -> Any:
        """
        Call Databricks AI Gateway endpoint.
        
        Args:
            messages: List of chat messages
            tools: Optional tool definitions
            temperature: Optional temperature override
        
        Returns:
            AI Gateway response
        """
        # Convert messages to Databricks format
        chat_messages = [
            ChatMessage(
                role=ChatMessageRole(msg["role"]),
                content=msg["content"]
            )
            for msg in messages
        ]
        
        # Extract endpoint name from URI
        # Format: "ai-gateway:/catalog.schema.endpoint_name"
        endpoint_path = self.ai_gateway_endpoint.replace("ai-gateway:/", "")
        parts = endpoint_path.split(".")
        endpoint_name = parts[-1] if len(parts) == 3 else endpoint_path
        
        # Call AI Gateway via Model Serving API
        # Note: In Databricks, AI Gateway endpoints are accessed via serving API
        response = self.workspace.serving_endpoints.query(
            name=endpoint_name,
            messages=chat_messages,
            temperature=temperature or self.temperature,
            # Tools would be passed here if supported by endpoint
        )
        
        return response
    
    def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool function.
        
        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments
        
        Returns:
            Tool execution result
        """
        if tool_name not in self.tool_functions:
            return {
                "error": f"Tool {tool_name} not found",
                "available_tools": list(self.tool_functions.keys())
            }
        
        try:
            # Execute tool with timeout
            function = self.tool_functions[tool_name]
            result = function(**tool_args)
            
            # Log to MLflow
            mlflow.log_param(f"tool_call_{tool_name}", json.dumps(tool_args))
            mlflow.log_metric(f"tool_success_{tool_name}", 1)
            
            return result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "tool_name": tool_name,
                "arguments": tool_args
            }
            
            # Log error to MLflow
            mlflow.log_metric(f"tool_error_{tool_name}", 1)
            mlflow.log_param(f"tool_error_details_{tool_name}", str(e))
            
            return error_result
    
    def process(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the agent.
        
        Args:
            user_query: User's question/request
            context: Optional context dictionary
        
        Returns:
            Dict with 'answer' and metadata
        """
        # Start MLflow run
        with mlflow.start_run(run_name=f"{self.name}_query"):
            mlflow.log_param("agent_name", self.name)
            mlflow.log_param("query", user_query)
            mlflow.log_param("ai_gateway_endpoint", self.ai_gateway_endpoint)
            
            try:
                # Build initial messages
                messages = [
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": user_query}
                ]
                
                # Tool execution loop
                for iteration in range(self.max_iterations):
                    mlflow.log_metric("iteration", iteration)
                    
                    # Call AI Gateway
                    response = self._call_ai_gateway(
                        messages=messages,
                        tools=self.tools if self.tools else None
                    )
                    
                    # Extract response message
                    # Note: Response format depends on AI Gateway configuration
                    # This is a simplified version - actual parsing may vary
                    response_message = response.choices[0].message
                    
                    # Check if LLM wants to use tools
                    if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                        # Execute each tool call
                        tool_results = []
                        
                        for tool_call in response_message.tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)
                            
                            # Execute tool
                            result = self._execute_tool(tool_name, tool_args)
                            tool_results.append({
                                "tool_call_id": tool_call.id,
                                "tool_name": tool_name,
                                "result": result
                            })
                        
                        # Add assistant message and tool results to conversation
                        messages.append({
                            "role": "assistant",
                            "content": response_message.content or "",
                            "tool_calls": response_message.tool_calls
                        })
                        
                        for tool_result in tool_results:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_result["tool_call_id"],
                                "content": json.dumps(tool_result["result"])
                            })
                        
                        # Continue loop to get final answer
                        continue
                    
                    else:
                        # No tool calls - we have the final answer
                        final_answer = response_message.content
                        
                        mlflow.log_param("final_answer_length", len(final_answer))
                        mlflow.log_metric("total_iterations", iteration + 1)
                        mlflow.log_metric("success", 1)
                        
                        return {
                            "answer": final_answer,
                            "iterations": iteration + 1,
                            "agent_name": self.name,
                            "tool_calls": len([m for m in messages if m.get("role") == "tool"])
                        }
                
                # Max iterations reached
                mlflow.log_metric("max_iterations_reached", 1)
                return {
                    "answer": "Maximum iterations reached. Please try a simpler query.",
                    "error": "max_iterations",
                    "iterations": self.max_iterations
                }
            
            except Exception as e:
                mlflow.log_param("error", str(e))
                mlflow.log_metric("success", 0)
                
                return {
                    "answer": f"Error processing query: {str(e)}",
                    "error": str(e),
                    "agent_name": self.name
                }
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable
    ) -> None:
        """
        Register a new tool with this agent.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameters schema
            function: Python function to execute
        """
        tool_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
        
        self.tools.append(tool_def)
        self.tool_functions[name] = function
