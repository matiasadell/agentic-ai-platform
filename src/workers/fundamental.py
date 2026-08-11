"""Fundamental Analysis Workers with Real APIs.

Workers integrated with:
- Alpha Vantage API (financial statements)
- Financial Modeling Prep API (ratios, earnings)
"""

import requests
from typing import Dict, Any, Optional, List
import os


# ============================================================================
# FINANCIAL STATEMENT WORKER - Alpha Vantage
# ============================================================================

class FinancialStatementWorker:
    """Analyzes financial statements using Alpha Vantage API."""
    
    def __init__(self):
        self.name = "FinancialStatementWorker"
        # Try settings first, fallback to environment variable
        try:
            from src.utils.config import settings
            self.api_key = settings.alpha_vantage_api_key
        except:
            self.api_key = os.environ.get('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = "https://www.alphavantage.co/query"
    
    def analyze_statements(
        self,
        ticker: str,
        query: str,
        period: str = "latest",
        statements: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze financial statements using Alpha Vantage."""
        statements = statements or ["balance", "income", "cashflow"]
        
        try:
            # Fetch data from Alpha Vantage
            balance_sheet = self._fetch_balance_sheet(ticker) if "balance" in statements else {}
            income_stmt = self._fetch_income_statement(ticker) if "income" in statements else {}
            cash_flow = self._fetch_cash_flow(ticker) if "cashflow" in statements else {}
            
            # Extract latest period
            latest_balance = balance_sheet.get("annualReports", [{}])[0] if balance_sheet.get("annualReports") else {}
            latest_income = income_stmt.get("annualReports", [{}])[0] if income_stmt.get("annualReports") else {}
            latest_cashflow = cash_flow.get("annualReports", [{}])[0] if cash_flow.get("annualReports") else {}
            
            # Parse to response format
            total_assets = self._safe_float(latest_balance.get("totalAssets"))
            total_liabilities = self._safe_float(latest_balance.get("totalLiabilities"))
            total_equity = self._safe_float(latest_balance.get("totalShareholderEquity"))
            revenue = self._safe_float(latest_income.get("totalRevenue"))
            net_income = self._safe_float(latest_income.get("netIncome"))
            operating_income = self._safe_float(latest_income.get("operatingIncome"))
            operating_cash_flow = self._safe_float(latest_cashflow.get("operatingCashflow"))
            fcf = self._calculate_fcf(latest_cashflow)
            
            return {
                "success": True,
                "worker_name": self.name,
                "query": query,
                "ticker": ticker.upper(),
                "period": latest_balance.get("fiscalDateEnding", period),
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "total_equity": total_equity,
                "revenue": revenue,
                "net_income": net_income,
                "operating_income": operating_income,
                "operating_cash_flow": operating_cash_flow,
                "free_cash_flow": fcf,
                "currency": "USD",
                "statements_count": len(statements),
                "summary": self._generate_summary(ticker, total_assets, revenue, net_income, fcf, latest_balance.get("fiscalDateEnding"))
            }
            
        except Exception as e:
            return self._error_response(ticker, query, e)
    
    def _fetch_balance_sheet(self, ticker: str) -> Dict[str, Any]:
        """Alpha Vantage: BALANCE_SHEET endpoint."""
        params = {"function": "BALANCE_SHEET", "symbol": ticker, "apikey": self.api_key}
        response = requests.get(self.base_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    
    def _fetch_income_statement(self, ticker: str) -> Dict[str, Any]:
        """Alpha Vantage: INCOME_STATEMENT endpoint."""
        params = {"function": "INCOME_STATEMENT", "symbol": ticker, "apikey": self.api_key}
        response = requests.get(self.base_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    
    def _fetch_cash_flow(self, ticker: str) -> Dict[str, Any]:
        """Alpha Vantage: CASH_FLOW endpoint."""
        params = {"function": "CASH_FLOW", "symbol": ticker, "apikey": self.api_key}
        response = requests.get(self.base_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    
    def _calculate_fcf(self, cashflow: Dict[str, Any]) -> float:
        """FCF = Operating Cash Flow - CapEx."""
        ocf = self._safe_float(cashflow.get("operatingCashflow"))
        capex = self._safe_float(cashflow.get("capitalExpenditures"))
        if ocf is not None and capex is not None:
            return ocf - abs(capex)
        return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Convert to float safely."""
        try:
            return float(value) if value else None
        except (ValueError, TypeError):
            return None
    
    def _generate_summary(self, ticker, assets, revenue, net_income, fcf, period) -> str:
        period_str = period or "N/A"
        assets_str = f"${assets:,.0f}" if assets else "N/A"
        revenue_str = f"${revenue:,.0f}" if revenue else "N/A"
        net_income_str = f"${net_income:,.0f}" if net_income else "N/A"
        fcf_str = f"${fcf:,.0f}" if fcf else "N/A"
        
        return (
            f"Financial statement analysis for {ticker.upper()} (period: {period_str}). "
            f"Total assets: {assets_str}, Revenue: {revenue_str}, "
            f"Net income: {net_income_str}, Free cash flow: {fcf_str}. "
            f"Data from Alpha Vantage API."
        )
    
    def _error_response(self, ticker, query, error):
        return {
            "success": False,
            "worker_name": self.name,
            "query": query,
            "ticker": ticker.upper(),
            "error": str(error),
            "error_type": type(error).__name__,
            "summary": f"Failed to fetch financial statements for {ticker}: {str(error)}"
        }


# ============================================================================
# KEY RATIOS WORKER - Financial Modeling Prep
# ============================================================================

class KeyRatiosWorker:
    """Calculates key financial ratios using Financial Modeling Prep API."""
    
    def __init__(self):
        self.name = "KeyRatiosWorker"
        # Try settings first, fallback to environment variable
        try:
            from src.utils.config import settings
            self.api_key = settings.fmp_api_key
        except:
            self.api_key = os.environ.get('FMP_API_KEY', 'demo')
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    def calculate_ratios(
        self,
        ticker: str,
        query: str,
        ratio_categories: List[str] = None
    ) -> Dict[str, Any]:
        """Calculate financial ratios using FMP API."""
        ratio_categories = ratio_categories or ["valuation", "profitability", "liquidity", "efficiency"]
        
        try:
            # Fetch ratios from FMP
            ratios_ttm = self._fetch_ratios_ttm(ticker)
            
            # Extract latest data
            ratios = ratios_ttm[0] if ratios_ttm and isinstance(ratios_ttm, list) else {}
            
            return {
                "success": True,
                "worker_name": self.name,
                "query": query,
                "ticker": ticker.upper(),
                # Valuation Ratios
                "pe_ratio": ratios.get("priceEarningsRatioTTM"),
                "pb_ratio": ratios.get("priceToBookRatioTTM"),
                "ps_ratio": ratios.get("priceToSalesRatioTTM"),
                # Profitability Ratios
                "roe": ratios.get("returnOnEquityTTM"),
                "roa": ratios.get("returnOnAssetsTTM"),
                "profit_margin": ratios.get("netProfitMarginTTM"),
                # Liquidity Ratios
                "current_ratio": ratios.get("currentRatioTTM"),
                "quick_ratio": ratios.get("quickRatioTTM"),
                # Efficiency Ratios
                "asset_turnover": ratios.get("assetTurnoverTTM"),
                "inventory_turnover": ratios.get("inventoryTurnoverTTM"),
                "ratios_calculated": len([v for v in ratios.values() if v is not None]),
                "benchmark_comparison": self._generate_benchmark(ratios),
                "summary": self._generate_summary(ticker, ratios)
            }
            
        except Exception as e:
            return self._error_response(ticker, query, e)
    
    def _fetch_ratios_ttm(self, ticker: str) -> List[Dict[str, Any]]:
        """FMP: ratios-ttm endpoint (trailing twelve months)."""
        url = f"{self.base_url}/ratios-ttm/{ticker}"
        params = {"apikey": self.api_key}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    
    def _generate_benchmark(self, ratios) -> str:
        pe = ratios.get("priceEarningsRatioTTM", 0) or 0
        roe = ratios.get("returnOnEquityTTM", 0) or 0
        
        benchmark = []
        if pe > 30:
            benchmark.append(f"P/E ratio ({pe:.1f}) above market average")
        if roe > 20:
            benchmark.append(f"ROE ({roe:.1f}%) above industry average")
        
        return ". ".join(benchmark) if benchmark else "Ratios within normal range"
    
    def _generate_summary(self, ticker, ratios) -> str:
        pe = ratios.get("priceEarningsRatioTTM", 0) or 0
        roe = ratios.get("returnOnEquityTTM", 0) or 0
        current = ratios.get("currentRatioTTM", 0) or 0
        
        return (
            f"Key ratio analysis for {ticker.upper()}. "
            f"P/E: {pe:.1f}, ROE: {roe:.1f}%, Current Ratio: {current:.2f}. "
            f"Data from Financial Modeling Prep API."
        )
    
    def _error_response(self, ticker, query, error):
        return {
            "success": False,
            "worker_name": self.name,
            "query": query,
            "ticker": ticker.upper(),
            "error": str(error),
            "error_type": type(error).__name__,
            "summary": f"Failed to fetch ratios for {ticker}: {str(error)}"
        }


# ============================================================================
# EARNINGS WORKER - Financial Modeling Prep
# ============================================================================

class EarningsWorker:
    """Analyzes earnings using Financial Modeling Prep API."""
    
    def __init__(self):
        self.name = "EarningsWorker"
        # Try settings first, fallback to environment variable
        try:
            from src.utils.config import settings
            self.api_key = settings.fmp_api_key
        except:
            self.api_key = os.environ.get('FMP_API_KEY', 'demo')
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    def analyze_earnings(
        self,
        ticker: str,
        query: str,
        quarters: int = 1
    ) -> Dict[str, Any]:
        """Analyze earnings using FMP API."""
        try:
            # Fetch earnings data
            earnings_surprises = self._fetch_earnings_surprises(ticker)
            
            # Get latest quarter
            latest_earnings = earnings_surprises[0] if earnings_surprises and isinstance(earnings_surprises, list) else {}
            
            # Calculate surprises
            eps_reported = latest_earnings.get("actualEarningResult")
            eps_estimated = latest_earnings.get("estimatedEarning")
            eps_surprise = None
            eps_surprise_pct = None
            
            if eps_reported is not None and eps_estimated is not None and eps_estimated != 0:
                eps_surprise = eps_reported - eps_estimated
                eps_surprise_pct = (eps_surprise / eps_estimated * 100)
            
            return {
                "success": True,
                "worker_name": self.name,
                "query": query,
                "ticker": ticker.upper(),
                "reporting_date": latest_earnings.get("date"),
                "eps_reported": eps_reported,
                "eps_estimated": eps_estimated,
                "eps_surprise": eps_surprise,
                "eps_surprise_percent": eps_surprise_pct,
                "revenue_reported": None,  # FMP free tier may not have this
                "revenue_estimated": None,
                "revenue_surprise_percent": None,
                "guidance_raised": None,
                "guidance_summary": "Check latest earnings call for guidance details",
                "analyst_rating": "Hold",
                "price_target": None,
                "earnings_calls_analyzed": quarters,
                "summary": self._generate_summary(ticker, latest_earnings, eps_surprise_pct)
            }
            
        except Exception as e:
            return self._error_response(ticker, query, e)
    
    def _fetch_earnings_surprises(self, ticker: str) -> List[Dict[str, Any]]:
        """FMP: earnings-surprises endpoint."""
        url = f"{self.base_url}/earnings-surprises/{ticker}"
        params = {"apikey": self.api_key}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    
    def _generate_summary(self, ticker, earnings, surprise_pct) -> str:
        date = earnings.get("date", "N/A")
        eps_reported = earnings.get("actualEarningResult", 0)
        eps_estimated = earnings.get("estimatedEarning", 0)
        
        if surprise_pct:
            beat_miss = "Beat" if surprise_pct > 0 else "Missed"
            return (
                f"Earnings analysis for {ticker.upper()} ({date}). "
                f"{beat_miss} EPS: ${eps_reported:.2f} vs ${eps_estimated:.2f} est. "
                f"Surprise: {abs(surprise_pct):.1f}%. Data from Financial Modeling Prep."
            )
        else:
            return f"Earnings data for {ticker.upper()} ({date}). Data from Financial Modeling Prep."
    
    def _error_response(self, ticker, query, error):
        return {
            "success": False,
            "worker_name": self.name,
            "query": query,
            "ticker": ticker.upper(),
            "error": str(error),
            "error_type": type(error).__name__,
            "summary": f"Failed to fetch earnings for {ticker}: {str(error)}"
        }


# ============================================================================
# VALUATION WORKER - Mock Data (DCF to be implemented)
# ============================================================================

class ValuationWorker:
    """DCF valuation - requires implementation."""
    
    def __init__(self):
        self.name = "ValuationWorker"
    
    def estimate_value(
        self,
        ticker: str,
        query: str,
        methods: List[str] = None,
        peer_tickers: List[str] = None
    ) -> Dict[str, Any]:
        """Estimate intrinsic value (mock data for now)."""
        methods = methods or ["dcf", "comparables"]
        peer_tickers = peer_tickers or ["RIVN", "LCID", "F", "GM"]
        
        current_price = 245.00
        
        return {
            "success": True,
            "worker_name": self.name,
            "query": query,
            "ticker": ticker.upper(),
            "current_price": current_price,
            "dcf_value": 285.00,
            "comparable_value": 270.00,
            "fair_value_estimate": 277.50,
            "upside_downside": ((277.50 - current_price) / current_price) * 100,
            "valuation_rating": "Undervalued",
            "discount_rate": 10.5,
            "terminal_growth_rate": 3.0,
            "peer_group": peer_tickers,
            "peer_average_pe": 32.5,
            "valuation_methods_used": len(methods),
            "confidence_level": "Medium",
            "summary": f"Valuation analysis for {ticker.upper()} (current: ${current_price}). "
                      f"DCF value: $285, Comparables value: $270, Fair value estimate: $277.50. "
                      f"Indicates 13.3% upside. Rating: Undervalued. Mock data - DCF to be implemented."
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "FinancialStatementWorker",
    "KeyRatiosWorker",
    "EarningsWorker",
    "ValuationWorker"
]
