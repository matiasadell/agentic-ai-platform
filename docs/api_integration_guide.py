"""
API INTEGRATION GUIDE - Fundamental Workers
===========================================

Este archivo contiene ejemplos completos de integración con APIs reales
para los 4 fundamental workers.

APIs CONFIGURADAS:
- ✅ Alpha Vantage: settings.alpha_vantage_api_key
- ✅ Financial Modeling Prep: settings.fmp_api_key = "fgx8EXmmbWI0g0C70PpA5PqSVhjPYmoR"
- ✅ SEC Edgar: NO requiere API key (solo User-Agent header)

"""

import requests
from typing import Dict, Any, List
from src.utils.config import settings


# ============================================================================
# 1. FINANCIAL STATEMENT WORKER - Alpha Vantage
# ============================================================================

class FinancialStatementWorker:
    """Analyzes financial statements using Alpha Vantage API."""
    
    def __init__(self):
        self.name = "FinancialStatementWorker"
        self.api_key = settings.alpha_vantage_api_key
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
            latest_balance = balance_sheet.get("annualReports", [{}])[0]
            latest_income = income_stmt.get("annualReports", [{}])[0]
            latest_cashflow = cash_flow.get("annualReports", [{}])[0]
            
            return {
                "success": True,
                "worker_name": self.name,
                "query": query,
                "ticker": ticker.upper(),
                "period": latest_balance.get("fiscalDateEnding", period),
                "total_assets": float(latest_balance.get("totalAssets", 0)),
                "total_liabilities": float(latest_balance.get("totalLiabilities", 0)),
                "total_equity": float(latest_balance.get("totalShareholderEquity", 0)),
                "revenue": float(latest_income.get("totalRevenue", 0)),
                "net_income": float(latest_income.get("netIncome", 0)),
                "operating_income": float(latest_income.get("operatingIncome", 0)),
                "operating_cash_flow": float(latest_cashflow.get("operatingCashflow", 0)),
                "free_cash_flow": self._calculate_fcf(latest_cashflow),
                "currency": "USD",
                "statements_count": len(statements),
                "summary": self._generate_summary(ticker, latest_balance, latest_income, latest_cashflow)
            }
            
        except Exception as e:
            return self._error_response(ticker, query, e)
    
    def _fetch_balance_sheet(self, ticker: str) -> Dict[str, Any]:
        """Alpha Vantage: BALANCE_SHEET endpoint."""
        params = {
            "function": "BALANCE_SHEET",
            "symbol": ticker,
            "apikey": self.api_key
        }
        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _fetch_income_statement(self, ticker: str) -> Dict[str, Any]:
        """Alpha Vantage: INCOME_STATEMENT endpoint."""
        params = {
            "function": "INCOME_STATEMENT",
            "symbol": ticker,
            "apikey": self.api_key
        }
        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _fetch_cash_flow(self, ticker: str) -> Dict[str, Any]:
        """Alpha Vantage: CASH_FLOW endpoint."""
        params = {
            "function": "CASH_FLOW",
            "symbol": ticker,
            "apikey": self.api_key
        }
        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _calculate_fcf(self, cashflow: Dict[str, Any]) -> float:
        """FCF = Operating Cash Flow - CapEx."""
        ocf = float(cashflow.get("operatingCashflow", 0))
        capex = float(cashflow.get("capitalExpenditures", 0))
        return ocf - abs(capex)
    
    def _generate_summary(self, ticker, balance, income, cashflow) -> str:
        period = balance.get("fiscalDateEnding", "N/A")
        assets = float(balance.get("totalAssets", 0))
        revenue = float(income.get("totalRevenue", 0))
        net_income = float(income.get("netIncome", 0))
        fcf = self._calculate_fcf(cashflow)
        
        return (
            f"Financial statement analysis for {ticker.upper()} (period: {period}). "
            f"Total assets: ${assets:,.0f}, Revenue: ${revenue:,.0f}, "
            f"Net income: ${net_income:,.0f}, Free cash flow: ${fcf:,.0f}. "
            f"Data from Alpha Vantage."
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
# 2. KEY RATIOS WORKER - Financial Modeling Prep
# ============================================================================

class KeyRatiosWorker:
    """Calculates key financial ratios using Financial Modeling Prep API."""
    
    def __init__(self):
        self.name = "KeyRatiosWorker"
        self.api_key = settings.fmp_api_key
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
            key_metrics = self._fetch_key_metrics(ticker)
            
            # Extract latest data
            ratios = ratios_ttm[0] if ratios_ttm else {}
            metrics = key_metrics[0] if key_metrics else {}
            
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
                "benchmark_comparison": self._generate_benchmark(ratios, metrics),
                "summary": self._generate_summary(ticker, ratios, metrics)
            }
            
        except Exception as e:
            return self._error_response(ticker, query, e)
    
    def _fetch_ratios_ttm(self, ticker: str) -> List[Dict[str, Any]]:
        """FMP: ratios-ttm endpoint (trailing twelve months)."""
        url = f"{self.base_url}/ratios-ttm/{ticker}"
        params = {"apikey": self.api_key}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _fetch_key_metrics(self, ticker: str) -> List[Dict[str, Any]]:
        """FMP: key-metrics-ttm endpoint."""
        url = f"{self.base_url}/key-metrics-ttm/{ticker}"
        params = {"apikey": self.api_key}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _generate_benchmark(self, ratios, metrics) -> str:
        pe = ratios.get("priceEarningsRatioTTM", 0)
        roe = ratios.get("returnOnEquityTTM", 0)
        
        benchmark = []
        if pe and pe > 30:
            benchmark.append(f"P/E ratio ({pe:.1f}) above market average")
        if roe and roe > 20:
            benchmark.append(f"ROE ({roe:.1f}%) above industry average")
        
        return ". ".join(benchmark) if benchmark else "Ratios within normal range"
    
    def _generate_summary(self, ticker, ratios, metrics) -> str:
        pe = ratios.get("priceEarningsRatioTTM", 0)
        roe = ratios.get("returnOnEquityTTM", 0)
        current = ratios.get("currentRatioTTM", 0)
        
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
# 3. EARNINGS WORKER - Financial Modeling Prep
# ============================================================================

class EarningsWorker:
    """Analyzes earnings using Financial Modeling Prep API."""
    
    def __init__(self):
        self.name = "EarningsWorker"
        self.api_key = settings.fmp_api_key
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
            analyst_estimates = self._fetch_analyst_estimates(ticker)
            
            # Get latest quarter
            latest_earnings = earnings_surprises[0] if earnings_surprises else {}
            latest_estimates = analyst_estimates[0] if analyst_estimates else {}
            
            # Calculate surprises
            eps_reported = latest_earnings.get("actualEarningResult", 0)
            eps_estimated = latest_earnings.get("estimatedEarning", 0)
            eps_surprise = eps_reported - eps_estimated if eps_reported and eps_estimated else None
            eps_surprise_pct = (eps_surprise / eps_estimated * 100) if eps_surprise and eps_estimated else None
            
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
                "guidance_raised": None,  # Would need earnings call transcripts
                "guidance_summary": "Check latest earnings call for guidance details",
                "analyst_rating": latest_estimates.get("analystRatingBuy", "Hold"),
                "price_target": latest_estimates.get("estimatedPriceAvg"),
                "earnings_calls_analyzed": quarters,
                "summary": self._generate_summary(ticker, latest_earnings, latest_estimates)
            }
            
        except Exception as e:
            return self._error_response(ticker, query, e)
    
    def _fetch_earnings_surprises(self, ticker: str) -> List[Dict[str, Any]]:
        """FMP: earnings-surprises endpoint."""
        url = f"{self.base_url}/earnings-surprises/{ticker}"
        params = {"apikey": self.api_key}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _fetch_analyst_estimates(self, ticker: str) -> List[Dict[str, Any]]:
        """FMP: analyst-estimates endpoint."""
        url = f"{self.base_url}/analyst-estimates/{ticker}"
        params = {"apikey": self.api_key, "limit": 1}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _generate_summary(self, ticker, earnings, estimates) -> str:
        date = earnings.get("date", "N/A")
        eps_reported = earnings.get("actualEarningResult", 0)
        eps_estimated = earnings.get("estimatedEarning", 0)
        surprise = eps_reported - eps_estimated if eps_reported and eps_estimated else 0
        
        beat_miss = "Beat" if surprise > 0 else "Missed"
        
        return (
            f"Earnings analysis for {ticker.upper()} ({date}). "
            f"{beat_miss} EPS: ${eps_reported:.2f} vs ${eps_estimated:.2f} est. "
            f"Surprise: ${surprise:.2f}. Data from Financial Modeling Prep."
        )
    
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
# 4. VALUATION WORKER - In-House DCF Implementation
# ============================================================================

class ValuationWorker:
    """DCF valuation using data from FinancialStatementWorker."""
    
    def __init__(self):
        self.name = "ValuationWorker"
    
    def estimate_value(
        self,
        ticker: str,
        query: str,
        methods: List[str] = None,
        peer_tickers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate intrinsic value.
        
        NOTE: This requires implementing a DCF model using:
        - Financial statements from FinancialStatementWorker
        - Ratios from KeyRatiosWorker
        
        For now, returns mock data. Real implementation would:
        1. Fetch financial data from FinancialStatementWorker
        2. Project future cash flows (3-5 years)
        3. Calculate WACC (cost of equity + cost of debt)
        4. Calculate terminal value
        5. Discount cash flows to present value
        """
        
        # TODO: Implement real DCF model
        # This is a placeholder showing the structure
        
        return {
            "success": True,
            "worker_name": self.name,
            "query": query,
            "ticker": ticker.upper(),
            "current_price": None,  # Would fetch from market data API
            "dcf_value": None,  # Would calculate using DCF model
            "comparable_value": None,  # Would calculate using peer multiples
            "fair_value_estimate": None,
            "upside_downside": None,
            "valuation_rating": "Not Implemented",
            "discount_rate": None,
            "terminal_growth_rate": None,
            "peer_group": peer_tickers or [],
            "peer_average_pe": None,
            "valuation_methods_used": 0,
            "confidence_level": "Low",
            "summary": f"Valuation analysis for {ticker.upper()} requires DCF implementation. "
                      f"Use financial data from FinancialStatementWorker and ratios from KeyRatiosWorker."
        }


# ============================================================================
# SEC EDGAR INTEGRATION (OPTIONAL - NO API KEY NEEDED)
# ============================================================================

class SECEdgarHelper:
    """
    Helper for SEC Edgar API.
    
    NO API KEY REQUIRED - Only needs User-Agent header.
    
    Useful for:
    - Company filings (10-Q, 10-K, 8-K)
    - XBRL financial data
    - CIK lookup
    """
    
    def __init__(self, user_agent: str = "YourCompany contact@example.com"):
        self.base_url = "https://data.sec.gov"
        self.headers = {"User-Agent": user_agent}
    
    def get_company_facts(self, cik: str) -> Dict[str, Any]:
        """
        Fetch all company facts (XBRL data).
        
        Args:
            cik: 10-digit CIK with leading zeros (e.g., "0000320193" for Apple)
        
        Returns:
            JSON with all XBRL facts
        """
        url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik}.json"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_company_concept(self, cik: str, taxonomy: str, tag: str) -> Dict[str, Any]:
        """
        Fetch single concept (e.g., AccountsPayable) for a company.
        
        Args:
            cik: 10-digit CIK
            taxonomy: "us-gaap" or "ifrs-full"
            tag: Concept tag (e.g., "AccountsPayableCurrent")
        
        Returns:
            JSON with concept data across all filings
        """
        url = f"{self.base_url}/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_submissions(self, cik: str) -> Dict[str, Any]:
        """
        Fetch filing history for a company.
        
        Args:
            cik: 10-digit CIK
        
        Returns:
            JSON with all filings metadata
        """
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example 1: Financial Statements with Alpha Vantage
    print("\n" + "="*70)
    print("EXAMPLE 1: Financial Statements (Alpha Vantage)")
    print("="*70)
    
    fs_worker = FinancialStatementWorker()
    result = fs_worker.analyze_statements(
        ticker="AAPL",
        query="Analyze Apple financial statements",
        statements=["balance", "income", "cashflow"]
    )
    print(f"Success: {result['success']}")
    print(f"Revenue: ${result.get('revenue', 0):,.0f}")
    print(f"Summary: {result['summary'][:100]}...")
    
    # Example 2: Key Ratios with Financial Modeling Prep
    print("\n" + "="*70)
    print("EXAMPLE 2: Key Ratios (Financial Modeling Prep)")
    print("="*70)
    
    ratios_worker = KeyRatiosWorker()
    result = ratios_worker.calculate_ratios(
        ticker="TSLA",
        query="Calculate Tesla financial ratios"
    )
    print(f"Success: {result['success']}")
    print(f"P/E Ratio: {result.get('pe_ratio', 'N/A')}")
    print(f"ROE: {result.get('roe', 'N/A')}%")
    print(f"Summary: {result['summary'][:100]}...")
    
    # Example 3: Earnings with Financial Modeling Prep
    print("\n" + "="*70)
    print("EXAMPLE 3: Earnings (Financial Modeling Prep)")
    print("="*70)
    
    earnings_worker = EarningsWorker()
    result = earnings_worker.analyze_earnings(
        ticker="NVDA",
        query="Did NVIDIA beat earnings?"
    )
    print(f"Success: {result['success']}")
    print(f"EPS Surprise: {result.get('eps_surprise_percent', 'N/A')}%")
    print(f"Summary: {result['summary'][:100]}...")
    
    # Example 4: SEC Edgar (NO API KEY)
    print("\n" + "="*70)
    print("EXAMPLE 4: SEC Edgar (No API Key)")
    print("="*70)
    
    sec = SECEdgarHelper(user_agent="MyCompany contact@example.com")
    # Apple CIK: 0000320193
    submissions = sec.get_submissions("0000320193")
    print(f"Company: {submissions['name']}")
    print(f"CIK: {submissions['cik']}")
    print(f"Total filings: {len(submissions['filings']['recent']['accessionNumber'])}")

