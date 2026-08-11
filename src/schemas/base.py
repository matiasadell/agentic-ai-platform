"""Base Pydantic schemas for all worker responses.

Estos schemas garantizan:
- Validación automática de tipos en runtime
- Estructura consistente de respuestas
- Error handling estandarizado
- Serialización JSON automática
- Documentación viva del contrato
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class WorkerStatus(str, Enum):
    """Status de ejecución de un worker."""
    SUCCESS = "success"
    PARTIAL = "partial"  # Datos parciales disponibles
    FAILED = "failed"


class WorkerResponse(BaseModel):
    """Schema base para TODAS las respuestas de workers.
    
    Todos los workers deben retornar un objeto que hereda de este schema.
    Garantiza estructura consistente y permite graceful degradation.
    
    Attributes:
        success: Si el worker completó exitosamente
        worker_name: Nombre del worker que generó la respuesta
        query: Query original del usuario
        timestamp: Timestamp de ejecución
        execution_time: Tiempo de ejecución en segundos
        error: Mensaje de error (si success=False)
        error_type: Tipo de error para categorización
        metadata: Metadata adicional específica del worker
    """
    
    success: bool
    worker_name: str
    query: str
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time: Optional[float] = Field(None, ge=0)
    error: Optional[str] = None
    error_type: Optional[str] = None  # "VALIDATION_ERROR", "API_ERROR", "TIMEOUT", etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('worker_name')
    @classmethod
    def validate_worker_name(cls, v: str) -> str:
        """Asegurar que worker_name no esté vacío."""
        if not v or not v.strip():
            raise ValueError("worker_name no puede estar vacío")
        return v.strip()
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Asegurar que query no esté vacío."""
        if not v or not v.strip():
            raise ValueError("query no puede estar vacío")
        return v.strip()
    
    @field_validator('error')
    @classmethod
    def validate_error_consistency(cls, v: Optional[str], info) -> Optional[str]:
        """Si success=False, error debe estar presente."""
        success = info.data.get('success')
        if success is False and not v:
            raise ValueError("Si success=False, debe proporcionar un mensaje de error")
        return v
    
    class Config:
        """Configuración de Pydantic."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class SupervisorState(BaseModel):
    """Estado interno de un Supervisor (Level 2).
    
    Usado por MacroSupervisor, NewsSupervisor, FundamentalSupervisor.
    """
    
    query: str
    days: int = Field(gt=0, le=365, default=7)
    parallel: bool = True
    worker_results: List[WorkerResponse] = Field(default_factory=list)
    routing_plan: Optional[Dict[str, Any]] = None
    synthesis: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("query no puede estar vacío")
        return v.strip()


class OrchestratorState(BaseModel):
    """Estado interno del Strategic Orchestrator (Level 1).
    
    Coordina múltiples supervisors.
    """
    
    query: str
    supervisors_used: List[str] = Field(default_factory=list)
    supervisor_results: List[Dict[str, Any]] = Field(default_factory=list)
    plan: Optional[Dict[str, Any]] = None
    synthesis: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)