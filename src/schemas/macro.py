"""Schemas específicos para Macro Domain workers."""

from pydantic import Field, field_validator
from typing import Optional, List, Dict, Any
from .base import WorkerResponse


class MacroResponse(WorkerResponse):
    """Schema para MacroDataWorker responses.
    
    Hereda validación base y agrega campos específicos de datos macro.
    """
    
    # Datos macro específicos
    indicators: List[Dict[str, Any]] = Field(default_factory=list)
    trend: Optional[str] = None  # "bullish", "bearish", "neutral"
    summary: Optional[str] = None
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata específica de macro
    data_source: Optional[str] = Field(None, description="Fuente de datos (FRED, etc.)")
    indicators_count: int = Field(0, ge=0)
    time_range: Optional[str] = None
    
    @field_validator('indicators_count')
    @classmethod
    def validate_indicators_count(cls, v: int, info) -> int:
        """Validar que indicators_count coincida con len(indicators)."""
        indicators = info.data.get('indicators', [])
        if v != len(indicators):
            # Auto-corregir si es posible
            return len(indicators)
        return v


class RegionalResponse(WorkerResponse):
    """Schema para RegionalContextWorker responses."""
    
    regions: List[str] = Field(default_factory=list)
    regional_data: List[Dict[str, Any]] = Field(default_factory=list)
    comparison: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None


class TechnicalResponse(WorkerResponse):
    """Schema para IndicatorAnalysisWorker responses."""
    
    symbol: str
    indicators: Dict[str, Any] = Field(default_factory=dict)
    signals: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None  # "buy", "sell", "hold"
    confidence: Optional[float] = Field(None, ge=0, le=1)
    summary: Optional[str] = None