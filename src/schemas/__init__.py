"""Pydantic schemas para validación de worker responses.

Este módulo proporciona:
- Schemas base (WorkerResponse, SupervisorState, OrchestratorState)
- Schemas específicos por dominio (MacroResponse, SentimentResponse, etc.)
- Validación robusta con retry + fallback (WorkerValidator)
- Graceful degradation: siempre retorna objetos válidos

Uso:
    from src.schemas import WorkerValidator, SentimentResponse
    
    validator = WorkerValidator()
    result = validator.execute_with_validation(
        worker=sentiment_worker,
        method="analyze_sentiment",
        params={"query": "market", "days_back": 7},
        response_schema=SentimentResponse
    )
    # result es SIEMPRE un SentimentResponse válido
"""

from .base import WorkerResponse, WorkerStatus, SupervisorState, OrchestratorState
from .macro import MacroResponse, RegionalResponse, TechnicalResponse
from .news import SentimentResponse, NewsResponse, SectorResponse, EventResponse
from .fundamental import (
    FinancialStatementResponse,
    KeyRatiosResponse,
    EarningsResponse,
    ValuationResponse,
)
from .validator import WorkerValidator

__all__ = [
    # Base
    "WorkerResponse",
    "WorkerStatus",
    "SupervisorState",
    "OrchestratorState",
    # Macro
    "MacroResponse",
    "RegionalResponse",
    "TechnicalResponse",
    # News
    "SentimentResponse",
    "NewsResponse",
    "SectorResponse",
    "EventResponse",
    # Fundamental
    "FinancialStatementResponse",
    "KeyRatiosResponse",
    "EarningsResponse",
    "ValuationResponse",
    # Validator
    "WorkerValidator",
]