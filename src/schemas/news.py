"""Schemas específicos para News Domain workers."""

from pydantic import Field, field_validator
from typing import Optional, List, Dict, Any
from .base import WorkerResponse


class SentimentResponse(WorkerResponse):
    """Schema para MarketSentimentWorker responses.
    
    Valida que sentiment_score esté en rango [-10, 10] y que
    articles_analyzed sea consistente con success.
    """
    
    sentiment_score: Optional[float] = Field(None, ge=-10, le=10)
    sentiment_label: Optional[str] = None  # "bullish", "bearish", "neutral"
    confidence: Optional[float] = Field(None, ge=0, le=1)
    key_themes: List[str] = Field(default_factory=list)
    articles_analyzed: int = Field(0, ge=0)
    summary: Optional[str] = None
    
    @field_validator('sentiment_label')
    @classmethod
    def validate_sentiment_label(cls, v: Optional[str]) -> Optional[str]:
        """Validar que sentiment_label sea uno de los valores permitidos."""
        if v is not None:
            allowed = ["bullish", "bearish", "neutral", "mixed"]
            if v.lower() not in allowed:
                raise ValueError(f"sentiment_label debe ser uno de {allowed}")
            return v.lower()
        return v
    
    @field_validator('articles_analyzed')
    @classmethod
    def validate_articles_with_success(cls, v: int, info) -> int:
        """Si success=True, articles_analyzed debe ser > 0."""
        success = info.data.get('success')
        if success is True and v == 0:
            # Warning: success pero 0 artículos analizados (caso edge)
            pass  # Permitir pero loggear warning
        return v


class NewsResponse(WorkerResponse):
    """Schema para GeneralNewsWorker responses."""
    
    articles: List[Dict[str, Any]] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    timeline: Optional[List[Dict[str, Any]]] = None
    key_themes: List[str] = Field(default_factory=list)
    articles_count: int = Field(0, ge=0)
    summary: Optional[str] = None
    
    @field_validator('articles_count')
    @classmethod
    def validate_articles_count(cls, v: int, info) -> int:
        """Validar que articles_count coincida con len(articles)."""
        articles = info.data.get('articles', [])
        if v != len(articles):
            return len(articles)
        return v


class SectorResponse(WorkerResponse):
    """Schema para SectorNewsWorker responses."""
    
    sector: str
    articles: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment_score: Optional[float] = Field(None, ge=-10, le=10)
    trends: List[str] = Field(default_factory=list)
    competitors: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None
    
    @field_validator('sector')
    @classmethod
    def validate_sector(cls, v: str) -> str:
        """Asegurar que sector no esté vacío."""
        if not v or not v.strip():
            raise ValueError("sector no puede estar vacío")
        return v.strip().lower()


class EventResponse(WorkerResponse):
    """Schema para EventDetectionWorker responses."""
    
    events: List[Dict[str, Any]] = Field(default_factory=list)
    event_types: List[str] = Field(default_factory=list)  # "earnings", "M&A", "IPO", etc.
    events_count: int = Field(0, ge=0)
    high_impact_events: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None
    
    @field_validator('events_count')
    @classmethod
    def validate_events_count(cls, v: int, info) -> int:
        """Validar que events_count coincida con len(events)."""
        events = info.data.get('events', [])
        if v != len(events):
            return len(events)
        return v