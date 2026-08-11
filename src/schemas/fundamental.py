"""Pydantic schemas for Fundamental Analysis workers.

Domain-specific response schemas for financial statement analysis,
key ratios, earnings, and valuation workers.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from src.schemas.base import WorkerResponse


# ============================================================================
# FINANCIAL STATEMENT WORKER SCHEMA
# ============================================================================

class FinancialStatementResponse(WorkerResponse):
    """Response schema for FinancialStatementWorker.
    
    Includes balance sheet, income statement, and cash flow data.
    """
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    period: Optional[str] = Field(None, description="Reporting period (Q1 2024, FY2023, etc.)")
    
    # Balance Sheet
    total_assets: Optional[float] = Field(None, ge=0, description="Total assets ($)")
    total_liabilities: Optional[float] = Field(None, ge=0, description="Total liabilities ($)")
    total_equity: Optional[float] = Field(None, description="Shareholders equity ($)")
    
    # Income Statement
    revenue: Optional[float] = Field(None, ge=0, description="Total revenue ($)")
    net_income: Optional[float] = Field(None, description="Net income ($)")
    operating_income: Optional[float] = Field(None, description="Operating income ($)")
    
    # Cash Flow
    operating_cash_flow: Optional[float] = Field(None, description="Cash from operations ($)")
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow ($)")
    
    # Metadata
    currency: Optional[str] = Field("USD", description="Currency")
    statements_count: int = Field(0, ge=0, description="Number of statements analyzed")


# ============================================================================
# KEY RATIOS WORKER SCHEMA
# ============================================================================

class KeyRatiosResponse(WorkerResponse):
    """Response schema for KeyRatiosWorker.
    
    Financial ratios: valuation, profitability, liquidity, efficiency.
    """
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    
    # Valuation Ratios
    pe_ratio: Optional[float] = Field(None, ge=0, description="Price-to-Earnings ratio")
    pb_ratio: Optional[float] = Field(None, ge=0, description="Price-to-Book ratio")
    ps_ratio: Optional[float] = Field(None, ge=0, description="Price-to-Sales ratio")
    
    # Profitability Ratios
    roe: Optional[float] = Field(None, ge=-100, le=200, description="Return on Equity (%)")
    roa: Optional[float] = Field(None, ge=-100, le=100, description="Return on Assets (%)")
    profit_margin: Optional[float] = Field(None, ge=-100, le=100, description="Net profit margin (%)")
    
    # Liquidity Ratios
    current_ratio: Optional[float] = Field(None, ge=0, description="Current ratio")
    quick_ratio: Optional[float] = Field(None, ge=0, description="Quick ratio")
    
    # Efficiency Ratios
    asset_turnover: Optional[float] = Field(None, ge=0, description="Asset turnover")
    inventory_turnover: Optional[float] = Field(None, ge=0, description="Inventory turnover")
    
    # Metadata
    ratios_calculated: int = Field(0, ge=0, description="Number of ratios calculated")
    benchmark_comparison: Optional[str] = Field(None, description="Comparison vs industry/market")
    
    @field_validator("pe_ratio", "pb_ratio", "ps_ratio")
    @classmethod
    def validate_valuation_ratios(cls, v):
        """Validate valuation ratios are reasonable."""
        if v is not None and v < 0:
            raise ValueError("Valuation ratios must be non-negative")
        if v is not None and v > 1000:
            raise ValueError("Valuation ratio seems unreasonably high (>1000)")
        return v


# ============================================================================
# EARNINGS WORKER SCHEMA
# ============================================================================

class EarningsResponse(WorkerResponse):
    """Response schema for EarningsWorker.
    
    Earnings reports, guidance, surprises, analyst expectations.
    """
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    reporting_date: Optional[str] = Field(None, description="Earnings report date")
    
    # Reported Earnings
    eps_reported: Optional[float] = Field(None, description="Reported EPS ($)")
    eps_estimated: Optional[float] = Field(None, description="Analyst estimated EPS ($)")
    eps_surprise: Optional[float] = Field(None, description="EPS surprise (reported - estimated)")
    eps_surprise_percent: Optional[float] = Field(None, ge=-100, le=500, description="EPS surprise %")
    
    # Revenue
    revenue_reported: Optional[float] = Field(None, ge=0, description="Reported revenue ($)")
    revenue_estimated: Optional[float] = Field(None, ge=0, description="Estimated revenue ($)")
    revenue_surprise_percent: Optional[float] = Field(None, ge=-100, le=500, description="Revenue surprise %")
    
    # Guidance
    guidance_raised: Optional[bool] = Field(None, description="Did company raise guidance?")
    guidance_summary: Optional[str] = Field(None, description="Summary of forward guidance")
    
    # Analyst Sentiment
    analyst_rating: Optional[str] = Field(None, description="Average analyst rating (Buy/Hold/Sell)")
    price_target: Optional[float] = Field(None, ge=0, description="Average analyst price target ($)")
    
    # Metadata
    earnings_calls_analyzed: int = Field(0, ge=0, description="Number of earnings calls/transcripts analyzed")


# ============================================================================
# VALUATION WORKER SCHEMA
# ============================================================================

class ValuationResponse(WorkerResponse):
    """Response schema for ValuationWorker.
    
    DCF models, comparables analysis, intrinsic value estimates.
    """
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    current_price: Optional[float] = Field(None, ge=0, description="Current stock price ($)")
    
    # Intrinsic Value Estimates
    dcf_value: Optional[float] = Field(None, ge=0, description="DCF intrinsic value per share ($)")
    comparable_value: Optional[float] = Field(None, ge=0, description="Comparables-based value ($)")
    fair_value_estimate: Optional[float] = Field(None, ge=0, description="Fair value estimate ($)")
    
    # Valuation Metrics
    upside_downside: Optional[float] = Field(None, ge=-100, le=500, description="Upside/downside vs current price (%)")
    valuation_rating: Optional[str] = Field(None, description="Undervalued/Fairly Valued/Overvalued")
    
    # DCF Assumptions
    discount_rate: Optional[float] = Field(None, ge=0, le=30, description="WACC / discount rate (%)")
    terminal_growth_rate: Optional[float] = Field(None, ge=-10, le=20, description="Terminal growth rate (%)")
    
    # Comparables
    peer_group: Optional[List[str]] = Field(None, description="Comparable companies analyzed")
    peer_average_pe: Optional[float] = Field(None, ge=0, description="Peer group average P/E")
    
    # Metadata
    valuation_methods_used: int = Field(0, ge=0, description="Number of valuation methods used")
    confidence_level: Optional[str] = Field(None, description="Confidence in valuation (Low/Medium/High)")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "FinancialStatementResponse",
    "KeyRatiosResponse",
    "EarningsResponse",
    "ValuationResponse"
]
