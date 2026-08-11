"""Configuration management for Databricks-native FinSight AI platform.

This configuration uses 100% Databricks native services:
- AI Gateway (Unity Catalog) for LLM routing (no LiteLLM)
- Databricks Agents with native MCP (no custom MCP servers)
- Model Serving / Apps for deployment (no FastAPI)
- Unity Catalog for governance and tools registry
"""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ============================================================================
    # DATABRICKS NATIVE CONFIGURATION
    # ============================================================================
    
    # Databricks Workspace
    databricks_host: str = Field(..., description="Databricks workspace URL")
    databricks_token: str = Field(..., description="Databricks access token")
    
    # Unity Catalog (governance + tools registry)
    databricks_catalog: str = Field(default="main")
    databricks_schema: str = Field(default="finsight_ai")
    
    # AI Gateway Endpoints (replaces LiteLLM)
    # Format: ai-gateway:/catalog.schema.endpoint_name
    ai_gateway_synthesis: str = Field(
        default="ai-gateway:/main.finsight_ai.synthesis",
        description="AI Gateway endpoint for synthesis tasks (GPT-4o)"
    )
    ai_gateway_analysis: str = Field(
        default="ai-gateway:/main.finsight_ai.analysis",
        description="AI Gateway endpoint for analysis tasks (Claude)"
    )
    ai_gateway_extraction: str = Field(
        default="ai-gateway:/main.finsight_ai.extraction",
        description="AI Gateway endpoint for data extraction"
    )
    ai_gateway_grading: str = Field(
        default="ai-gateway:/main.finsight_ai.grading",
        description="AI Gateway endpoint for RAG grading"
    )
    ai_gateway_classification: str = Field(
        default="ai-gateway:/main.finsight_ai.classification",
        description="AI Gateway endpoint for classification"
    )
    
    # Vector Search
    vector_search_endpoint: str = Field(
        default="finsight_vector_search",
        description="Databricks Vector Search endpoint name"
    )
    vector_search_index: str = Field(
        default="main.finsight_ai.documents_index",
        description="Vector Search index (catalog.schema.index_name)"
    )
    
    # Model Serving (for agent deployment)
    model_serving_endpoint: str = Field(
        default="finsight-orchestrator",
        description="Model Serving endpoint name for orchestrator agent"
    )
    
    # SQL Warehouse (for data queries)
    sql_warehouse_id: str = Field(
        ...,
        description="SQL Warehouse ID for running queries"
    )
    
    # ============================================================================
    # EXTERNAL APIs (for financial data sources)
    # ============================================================================
    
    # LLM Provider Keys (managed by AI Gateway, but needed for setup)
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (configured in AI Gateway)"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key (configured in AI Gateway)"
    )
    
    # Financial Data APIs (external data sources)
    alpha_vantage_api_key: str = Field(..., description="Alpha Vantage API key")
    fmp_api_key: str = Field(..., description="Financial Modeling Prep API key")
    sec_api_key: Optional[str] = Field(default=None, description="SEC API key (optional)")
    news_api_key: str = Field(..., description="NewsAPI key")
    tavily_api_key: str = Field(..., description="Tavily API key for web search")
    
    # ============================================================================
    # DATABRICKS OBSERVABILITY (native, no external services needed)
    # ============================================================================
    
    # MLflow (nativo de Databricks)
    mlflow_tracking_uri: str = Field(
        default="databricks",
        description="Always 'databricks' for Databricks-hosted MLflow"
    )
    mlflow_experiment_name: str = Field(
        default="/Users/shared/finsight-ai-experiments",
        description="MLflow experiment path"
    )
    
    # LangSmith (opcional, solo para tracing adicional)
    langchain_tracing_v2: bool = Field(
        default=False,
        description="Enable LangSmith tracing (optional, use Databricks native instead)"
    )
    langchain_api_key: Optional[str] = Field(
        default=None,
        description="LangSmith API key (optional)"
    )
    langchain_project: str = Field(default="finsight-ai")
    
    # ============================================================================
    # OPTIONAL EXTERNAL SERVICES (can be replaced with Databricks alternatives)
    # ============================================================================
    
    # Neo4j (Knowledge Graph) - Could use Databricks SQL Graph features instead
    neo4j_uri: Optional[str] = Field(
        default=None,
        description="Neo4j URI (optional, can use Databricks SQL for graph queries)"
    )
    neo4j_user: Optional[str] = Field(default=None)
    neo4j_password: Optional[str] = Field(default=None)
    neo4j_database: str = Field(default="neo4j")
    
    # Redis (Caching) - Could use Databricks Delta cache or Photon instead
    redis_host: Optional[str] = Field(
        default=None,
        description="Redis host (optional, can use Delta cache)"
    )
    redis_port: int = Field(default=6379)
    redis_password: Optional[str] = Field(default=None)
    redis_db: int = Field(default=0)
    redis_ttl: int = Field(default=3600)
    
    # ============================================================================
    # AGENT CONFIGURATION
    # ============================================================================
    
    # Agent behavior
    max_agent_iterations: int = Field(
        default=10,
        description="Maximum iterations for agent loops"
    )
    agent_timeout: int = Field(
        default=300,
        description="Agent timeout in seconds"
    )
    
    # Human-in-the-loop
    human_approval_threshold: float = Field(
        default=100.0,
        description="Confidence threshold for human approval"
    )
    max_iterations: int = Field(default=5)
    timeout_seconds: int = Field(default=600)
    
    # ============================================================================
    # RAG CONFIGURATION
    # ============================================================================
    
    # Chunking
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    
    # Retrieval
    top_k_retrieval: int = Field(default=5)
    similarity_threshold: float = Field(default=0.7)
    
    # Guardrails
    enable_input_guardrails: bool = Field(default=True)
    enable_output_guardrails: bool = Field(default=True)
    financial_advice_warning: bool = Field(default=True)
    
    # ============================================================================
    # EVALUATION & TESTING
    # ============================================================================
    
    # RAGAS evaluation metrics
    ragas_metrics: List[str] = Field(
        default=["faithfulness", "answer_relevance", "context_precision"],
        description="RAGAS metrics to evaluate"
    )
    
    # Golden dataset (stored in Unity Catalog)
    golden_dataset_table: str = Field(
        default="main.finsight_ai.golden_dataset",
        description="Unity Catalog table with golden dataset"
    )
    evaluation_batch_size: int = Field(default=10)
    
    # ============================================================================
    # APPLICATION SETTINGS
    # ============================================================================
    
    # Logging
    log_level: str = Field(default="INFO")
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False)
    
    # Databricks App settings (if deploying as App)
    app_port: int = Field(
        default=8501,
        description="Port for Databricks App (Streamlit default)"
    )


# Global settings instance
settings = Settings()
