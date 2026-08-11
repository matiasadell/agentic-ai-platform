"""Fundamental Analysis Agents with LangGraph.

True multi-agent hierarchical architecture:
- Each agent is a create_react_agent with its own LLM
- Agents use LangChain tools (not raw HTTP calls)
- Supervisor coordinates agents using create_supervisor
- Each agent can reason and iterate

Follows the pattern from 8-multiagent notebook.
"""

import requests
import os
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model


# ============================================================================
# TOOLS - LangChain Tools for API calls
# ============================================================================

@tool
def fetch_financial_statements(ticker: str) -> str:
    """Fetch financial statements (balance sheet, income statement, cash flow) from Alpha Vantage API.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        String with formatted financial data
    """
    try:
        from src.utils.config import settings
        api_key = settings.alpha_vantage_api_key
    except:
        api_key = os.environ.get('ALPHA_VANTAGE_API_KEY', 'demo')
    
    base_url = "https://www.alphavantage.co/query"
    
    try:
        # Fetch all three statements
        balance_params = {"function": "BALANCE_SHEET", "symbol": ticker, "apikey": api_key}
        income_params = {"function": "INCOME_STATEMENT", "symbol": ticker, "apikey": api_key}
        cashflow_params = {"function": "CASH_FLOW", "symbol": ticker, "apikey": api_key}
        
        balance_sheet = requests.get(base_url, params=balance_params, timeout=15).json()
        income_stmt = requests.get(base_url, params=income_params, timeout=15).json()
        cash_flow = requests.get(base_url, params=cashflow_params, timeout=15).json()
        
        # Extract latest period
        latest_balance = balance_sheet.get("annualReports", [{}])[0] if balance_sheet.get("annualReports") else {}
        latest_income = income_stmt.get("annualReports", [{}])[0] if income_stmt.get("annualReports") else {}
        latest_cashflow = cash_flow.get("annualReports", [{}])[0] if cash_flow.get("annualReports") else {}
        
        # Parse key metrics
        def safe_float(v):
            try:
                return float(v) if v else None
            except:
                return None
        
        total_assets = safe_float(latest_balance.get("totalAssets"))
        total_liabilities = safe_float(latest_balance.get("totalLiabilities"))
        total_equity = safe_float(latest_balance.get("totalShareholderEquity"))
        revenue = safe_float(latest_income.get("totalRevenue"))
        net_income = safe_float(latest_income.get("netIncome"))
        operating_income = safe_float(latest_income.get("operatingIncome"))
        operating_cash_flow = safe_float(latest_cashflow.get("operatingCashflow"))
        capex = safe_float(latest_cashflow.get("capitalExpenditures"))
        
        fcf = None
        if operating_cash_flow and capex:
            fcf = operating_cash_flow - abs(capex)
        
        period = latest_balance.get("fiscalDateEnding", "N/A")
        
        # Format result
        result = f"""Financial Statements for {ticker.upper()} (Period: {period}):

Balance Sheet:
- Total Assets: ${total_assets:,.0f}" if total_assets else "N/A"
- Total Liabilities: ${total_liabilities:,.0f}" if total_liabilities else "N/A"
- Total Equity: ${total_equity:,.0f}" if total_equity else "N/A"

Income Statement:
- Revenue: ${revenue:,.0f}" if revenue else "N/A"
- Operating Income: ${operating_income:,.0f}" if operating_income else "N/A"
- Net Income: ${net_income:,.0f}" if net_income else "N/A"

Cash Flow:
- Operating Cash Flow: ${operating_cash_flow:,.0f}" if operating_cash_flow else "N/A"
- Free Cash Flow: ${fcf:,.0f}" if fcf else "N/A"

Data source: Alpha Vantage API
"""
        return result
        
    except Exception as e:
        return f"Error fetching financial statements for {ticker}: {str(e)}"


@tool
def fetch_key_ratios(ticker: str) -> str:
    """Fetch key financial ratios (valuation, profitability, liquidity) from Financial Modeling Prep API.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        String with formatted ratio data
    """
    try:
        from src.utils.config import settings
        api_key = settings.fmp_api_key
    except:
        api_key = os.environ.get('FMP_API_KEY', 'demo')
    
    base_url = "https://financialmodelingprep.com/api/v3"
    
    try:
        # Fetch ratios TTM
        url = f"{base_url}/ratios-ttm/{ticker}"
        params = {"apikey": api_key}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        ratios_data = response.json()
        
        # Extract latest
        ratios = ratios_data[0] if ratios_data and isinstance(ratios_data, list) else {}
        
        # Format result
        result = f"""Key Ratios for {ticker.upper()}:

Valuation Ratios:
- P/E Ratio: {ratios.get('priceEarningsRatioTTM', 'N/A')}
- P/B Ratio: {ratios.get('priceToBookRatioTTM', 'N/A')}
- P/S Ratio: {ratios.get('priceToSalesRatioTTM', 'N/A')}

Profitability Ratios:
- ROE: {ratios.get('returnOnEquityTTM', 'N/A')}%
- ROA: {ratios.get('returnOnAssetsTTM', 'N/A')}%
- Profit Margin: {ratios.get('netProfitMarginTTM', 'N/A')}%

Liquidity Ratios:
- Current Ratio: {ratios.get('currentRatioTTM', 'N/A')}
- Quick Ratio: {ratios.get('quickRatioTTM', 'N/A')}

Efficiency Ratios:
- Asset Turnover: {ratios.get('assetTurnoverTTM', 'N/A')}
- Inventory Turnover: {ratios.get('inventoryTurnoverTTM', 'N/A')}

Data source: Financial Modeling Prep API
"""
        return result
        
    except Exception as e:
        return f"Error fetching key ratios for {ticker}: {str(e)}"


@tool
def fetch_earnings_data(ticker: str) -> str:
    """Fetch earnings data (EPS surprises, beats/misses) from Financial Modeling Prep API.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        String with formatted earnings data
    """
    try:
        from src.utils.config import settings
        api_key = settings.fmp_api_key
    except:
        api_key = os.environ.get('FMP_API_KEY', 'demo')
    
    base_url = "https://financialmodelingprep.com/api/v3"
    
    try:
        # Fetch earnings surprises
        url = f"{base_url}/earnings-surprises/{ticker}"
        params = {"apikey": api_key}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        earnings_data = response.json()
        
        # Get latest quarter
        latest = earnings_data[0] if earnings_data and isinstance(earnings_data, list) else {}
        
        date = latest.get('date', 'N/A')
        actual_eps = latest.get('actualEarningResult', 0)
        estimated_eps = latest.get('estimatedEarning', 0)
        
        # Calculate surprise
        surprise = actual_eps - estimated_eps if actual_eps and estimated_eps else 0
        surprise_pct = (surprise / estimated_eps * 100) if estimated_eps else 0
        beat_miss = "Beat" if surprise > 0 else "Missed" if surprise < 0 else "Met"
        
        # Format result
        result = f"""Earnings Data for {ticker.upper()}:

Latest Quarter: {date}
- Actual EPS: ${actual_eps}
- Estimated EPS: ${estimated_eps}
- Surprise: ${surprise:.2f}
- Surprise %: {surprise_pct:.1f}%
- Result: {beat_miss} expectations

Data source: Financial Modeling Prep API
"""
        return result
        
    except Exception as e:
        return f"Error fetching earnings data for {ticker}: {str(e)}"


@tool
def calculate_valuation(ticker: str, revenue: float, net_income: float, fcf: float) -> str:
    """Calculate valuation metrics using DCF and comparables methods.
    
    Args:
        ticker: Stock ticker symbol
        revenue: Annual revenue
        net_income: Annual net income
        fcf: Free cash flow
    
    Returns:
        String with valuation analysis
    """
    # Simple mock DCF for now (to be implemented with real model)
    try:
        # Assume 10% discount rate, 5-year projection
        discount_rate = 0.10
        growth_rate = 0.05
        terminal_growth = 0.03
        
        # Project 5 years of FCF
        projected_fcfs = []
        for year in range(1, 6):
            projected_fcf = fcf * ((1 + growth_rate) ** year)
            discounted_fcf = projected_fcf / ((1 + discount_rate) ** year)
            projected_fcfs.append(discounted_fcf)
        
        # Terminal value
        terminal_fcf = fcf * ((1 + growth_rate) ** 5) * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        discounted_terminal = terminal_value / ((1 + discount_rate) ** 5)
        
        enterprise_value = sum(projected_fcfs) + discounted_terminal
        
        result = f"""Valuation Analysis for {ticker.upper()}:

DCF Model (Simplified):
- Discount Rate: {discount_rate*100:.1f}%
- Growth Rate: {growth_rate*100:.1f}%
- Terminal Growth: {terminal_growth*100:.1f}%
- Enterprise Value: ${enterprise_value:,.0f}

Comparables (Mock):
- Industry Avg P/E: 25x
- Industry Avg P/S: 3x

Note: This is a simplified model. Full DCF implementation pending.
"""
        return result
        
    except Exception as e:
        return f"Error calculating valuation for {ticker}: {str(e)}"


# ============================================================================
# AGENTS - create_react_agent instances
# ============================================================================

def create_financial_statement_agent(llm=None):
    """Create a ReAct agent for financial statement analysis.
    
    Uses Alpha Vantage API via LangChain tool.
    """
    if llm is None:
        llm = init_chat_model("openai:gpt-4o-mini")
    
    agent = create_react_agent(
        model=llm,
        tools=[fetch_financial_statements],
        prompt=(
            "You are a financial statement analyst agent.\n\n"
            "INSTRUCTIONS:\n"
            "- Analyze balance sheets, income statements, and cash flow statements\n"
            "- Use the fetch_financial_statements tool to get data from Alpha Vantage\n"
            "- Provide clear, concise analysis of financial health\n"
            "- Focus on key metrics: assets, liabilities, revenue, net income, FCF\n"
            "- After analysis, respond to the supervisor with your findings\n"
            "- Respond ONLY with analysis results, no extra text\n"
        ),
        name="financial_statement_agent"
    )
    
    return agent


def create_key_ratios_agent(llm=None):
    """Create a ReAct agent for financial ratio analysis.
    
    Uses Financial Modeling Prep API via LangChain tool.
    """
    if llm is None:
        llm = init_chat_model("openai:gpt-4o-mini")
    
    agent = create_react_agent(
        model=llm,
        tools=[fetch_key_ratios],
        prompt=(
            "You are a financial ratio analyst agent.\n\n"
            "INSTRUCTIONS:\n"
            "- Calculate and analyze valuation, profitability, liquidity ratios\n"
            "- Use the fetch_key_ratios tool to get data from FMP\n"
            "- Interpret ratios in context of industry standards\n"
            "- Focus on: P/E, ROE, ROA, Current Ratio, etc.\n"
            "- After analysis, respond to the supervisor with your findings\n"
            "- Respond ONLY with analysis results, no extra text\n"
        ),
        name="key_ratios_agent"
    )
    
    return agent


def create_earnings_agent(llm=None):
    """Create a ReAct agent for earnings analysis.
    
    Uses Financial Modeling Prep API via LangChain tool.
    """
    if llm is None:
        llm = init_chat_model("openai:gpt-4o-mini")
    
    agent = create_react_agent(
        model=llm,
        tools=[fetch_earnings_data],
        prompt=(
            "You are an earnings analyst agent.\n\n"
            "INSTRUCTIONS:\n"
            "- Analyze earnings reports, EPS surprises, beats/misses\n"
            "- Use the fetch_earnings_data tool to get data from FMP\n"
            "- Interpret earnings quality and guidance\n"
            "- Focus on: EPS actual vs estimated, surprise %, trends\n"
            "- After analysis, respond to the supervisor with your findings\n"
            "- Respond ONLY with analysis results, no extra text\n"
        ),
        name="earnings_agent"
    )
    
    return agent


def create_valuation_agent(llm=None):
    """Create a ReAct agent for valuation analysis.
    
    Uses in-house DCF model via LangChain tool.
    """
    if llm is None:
        llm = init_chat_model("openai:gpt-4o-mini")
    
    agent = create_react_agent(
        model=llm,
        tools=[calculate_valuation],
        prompt=(
            "You are a valuation analyst agent.\n\n"
            "INSTRUCTIONS:\n"
            "- Estimate intrinsic value using DCF and comparables\n"
            "- Use the calculate_valuation tool with revenue, income, FCF\n"
            "- Provide fair value estimates and over/undervaluation assessment\n"
            "- Focus on: DCF model, multiples, margin of safety\n"
            "- After analysis, respond to the supervisor with your findings\n"
            "- Respond ONLY with analysis results, no extra text\n"
        ),
        name="valuation_agent"
    )
    
    return agent


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'create_financial_statement_agent',
    'create_key_ratios_agent',
    'create_earnings_agent',
    'create_valuation_agent',
    'fetch_financial_statements',
    'fetch_key_ratios',
    'fetch_earnings_data',
    'calculate_valuation'
]
