
-- ===============================================================================
-- UC Functions for FinSight AI MCP Tools
-- ===============================================================================
-- 
-- This SQL file registers 5 Unity Catalog Functions that serve as MCP tools
-- for the AI Gateway endpoint: main.finsight_ai.finsight-chat
--
-- Functions:
--   1. get_gdp_data          → World Bank API - GDP data
--   2. get_inflation_data    → World Bank API - Inflation (CPI)
--   3. get_unemployment_data → World Bank API - Unemployment rate
--   4. get_interest_rate     → Placeholder - Interest rate (USA only)
--   5. get_financial_news    → NewsAPI - Financial news search
--
-- Prerequisites:
--   • Schema main.finsight_ai must exist
--   • NewsAPI key must be configured in Databricks Secrets (scope: finsight)
--   • Python requests library available in UC Functions environment
--
-- Usage:
--   1. Run this SQL file to register all functions
--   2. Test: SELECT main.finsight_ai.get_gdp_data('USA');
--   3. Connect to AI Gateway endpoint in /ml/ai-gateway/endpoints
--
-- ===============================================================================

-- Set catalog context
USE CATALOG main;

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS main.finsight_ai
COMMENT 'FinSight AI - Financial Intelligence Platform Tools';

-- ===============================================================================
-- FUNCTION 1: get_gdp_data
-- ===============================================================================
-- Get GDP data from World Bank API
-- Example: SELECT main.finsight_ai.get_gdp_data('Argentina');
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.get_gdp_data(country STRING)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Get GDP data for a country from World Bank API. Returns GDP in current US dollars. Example: get_gdp_data("USA") or get_gdp_data("Argentina")'
AS $$
import requests
import json
from datetime import datetime

# Country code mapping
country_map = {
    "usa": "USA",
    "united states": "USA",
    "argentina": "ARG",
    "china": "CHN",
    "germany": "DEU",
    "brazil": "BRA",
    "mexico": "MEX",
    "canada": "CAN",
    "uk": "GBR",
    "united kingdom": "GBR",
    "france": "FRA",
    "italy": "ITA",
    "spain": "ESP"
}

country_code = country_map.get(country.lower(), country.upper()[:3])

try:
    # World Bank API endpoint
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD"
    params = {
        "format": "json",
        "per_page": 5,
        "date": "2020:2024"  # Last 5 years
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if not data or len(data) < 2 or not data[1]:
        return json.dumps({
            "error": "No data available",
            "country": country,
            "message": "World Bank API did not return data for this country"
        })
    
    # Get most recent value
    latest_entry = data[1][0]
    value = latest_entry.get("value")
    year = latest_entry.get("date")
    
    if value is None:
        return json.dumps({
            "error": "No value available",
            "country": country
        })
    
    return json.dumps({
        "country": latest_entry.get("country", {}).get("value", country),
        "country_code": country_code,
        "gdp_usd": float(value),
        "year": year,
        "indicator": "GDP (current US$)",
        "source": "World Bank API",
        "retrieved_at": datetime.now().isoformat()
    })
    
except requests.exceptions.RequestException as e:
    return json.dumps({
        "error": "API request failed",
        "message": str(e),
        "country": country
    })
$$;

-- ===============================================================================
-- FUNCTION 2: get_inflation_data
-- ===============================================================================
-- Get inflation rate (CPI) from World Bank API
-- Example: SELECT main.finsight_ai.get_inflation_data('USA');
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.get_inflation_data(country STRING)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Get inflation rate (CPI) data for a country from World Bank API. Returns consumer price index annual percentage change. Example: get_inflation_data("Argentina")'
AS $$
import requests
import json
from datetime import datetime

country_map = {
    "usa": "USA",
    "united states": "USA",
    "argentina": "ARG",
    "china": "CHN",
    "germany": "DEU",
    "brazil": "BRA",
    "mexico": "MEX",
    "canada": "CAN"
}

country_code = country_map.get(country.lower(), country.upper()[:3])

try:
    # World Bank API - CPI inflation
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/FP.CPI.TOTL.ZG"
    params = {
        "format": "json",
        "per_page": 5,
        "date": "2020:2024"
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if not data or len(data) < 2 or not data[1]:
        return json.dumps({
            "error": "No data available",
            "country": country
        })
    
    latest_entry = data[1][0]
    value = latest_entry.get("value")
    year = latest_entry.get("date")
    
    if value is None:
        return json.dumps({
            "error": "No value available",
            "country": country
        })
    
    return json.dumps({
        "country": latest_entry.get("country", {}).get("value", country),
        "country_code": country_code,
        "inflation_rate": float(value),
        "year": year,
        "indicator": "Inflation, consumer prices (annual %)",
        "source": "World Bank API",
        "retrieved_at": datetime.now().isoformat()
    })
    
except requests.exceptions.RequestException as e:
    return json.dumps({
        "error": "API request failed",
        "message": str(e),
        "country": country
    })
$$;

-- ===============================================================================
-- FUNCTION 3: get_unemployment_data
-- ===============================================================================
-- Get unemployment rate from World Bank API
-- Example: SELECT main.finsight_ai.get_unemployment_data('USA');
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.get_unemployment_data(country STRING)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Get unemployment rate data for a country from World Bank API. Returns unemployment as percentage of total labor force. Example: get_unemployment_data("Germany")'
AS $$
import requests
import json
from datetime import datetime

country_map = {
    "usa": "USA",
    "united states": "USA",
    "argentina": "ARG",
    "germany": "DEU",
    "spain": "ESP",
    "france": "FRA"
}

country_code = country_map.get(country.lower(), country.upper()[:3])

try:
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/SL.UEM.TOTL.ZS"
    params = {
        "format": "json",
        "per_page": 5,
        "date": "2020:2024"
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if not data or len(data) < 2 or not data[1]:
        return json.dumps({
            "error": "No data available",
            "country": country
        })
    
    latest_entry = data[1][0]
    value = latest_entry.get("value")
    year = latest_entry.get("date")
    
    if value is None:
        return json.dumps({
            "error": "No value available",
            "country": country
        })
    
    return json.dumps({
        "country": latest_entry.get("country", {}).get("value", country),
        "country_code": country_code,
        "unemployment_rate": float(value),
        "year": year,
        "indicator": "Unemployment, total (% of total labor force)",
        "source": "World Bank API",
        "retrieved_at": datetime.now().isoformat()
    })
    
except requests.exceptions.RequestException as e:
    return json.dumps({
        "error": "API request failed",
        "message": str(e),
        "country": country
    })
$$;

-- ===============================================================================
-- FUNCTION 4: get_interest_rate
-- ===============================================================================
-- Get interest rate data (USA only, placeholder)
-- Example: SELECT main.finsight_ai.get_interest_rate('USA');
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.get_interest_rate(country_code STRING)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Get interest rate data. Currently supports USA Federal Funds Effective Rate (placeholder). Example: get_interest_rate("USA")'
AS $$
import json
from datetime import datetime

# TODO: Integrate with actual FRED API once API key is configured
# For now, return placeholder

if country_code.upper() == "USA":
    # Placeholder - would use FRED API in production
    return json.dumps({
        "country": "United States",
        "country_code": "USA",
        "interest_rate": 4.33,  # Current Fed Funds Rate (example)
        "date": datetime.now().strftime("%Y-%m-%d"),
        "indicator": "Federal Funds Effective Rate",
        "source": "Placeholder (FRED API integration pending)",
        "retrieved_at": datetime.now().isoformat()
    })
else:
    return json.dumps({
        "error": "Country not supported",
        "message": "Only USA is currently supported for interest rates",
        "country_code": country_code
    })
$$;

-- ===============================================================================
-- FUNCTION 5: get_financial_news
-- ===============================================================================
-- Get financial news from NewsAPI
-- Example: SELECT main.finsight_ai.get_financial_news('Tesla stock');
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.get_financial_news(
    api_key STRING,
    query STRING,
    from_date STRING,
    to_date STRING,
    language STRING,
    max_results INT
)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Search for financial news articles using NewsAPI. API key must be provided as first parameter (typically injected by AI Gateway from Databricks Secrets). Example: get_financial_news(api_key, "Tesla", null, null, "en", 5)'
AS $$
import requests
import json
from datetime import datetime, timedelta

# Validate API key
if not api_key or api_key.strip() == '':
    return json.dumps({
        "error": "NewsAPI key required",
        "message": "API key must be provided as first parameter"
    })

news_api_key = api_key

# Default dates
if not from_date:
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
if not to_date:
    to_date = datetime.now().strftime("%Y-%m-%d")
if not language:
    language = "en"
if not max_results:
    max_results = 5

try:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date,
        "to": to_date,
        "language": language,
        "sortBy": "relevancy",
        "pageSize": max_results,
        "apiKey": news_api_key
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if data.get("status") != "ok":
        return json.dumps({
            "error": "NewsAPI request failed",
            "message": data.get("message", "Unknown error"),
            "query": query
        })
    
    articles = data.get("articles", [])
    
    # Format articles
    formatted_articles = []
    for article in articles:
        formatted_articles.append({
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "url": article.get("url", ""),
            "published_at": article.get("publishedAt", ""),
            "content": article.get("content", "")[:500]  # Truncate for brevity
        })
    
    return json.dumps({
        "query": query,
        "total_results": data.get("totalResults", 0),
        "articles": formatted_articles,
        "from_date": from_date,
        "to_date": to_date,
        "retrieved_at": datetime.now().isoformat()
    })
    
except requests.exceptions.RequestException as e:
    return json.dumps({
        "error": "API request failed",
        "message": str(e),
        "query": query
    })
$$;

-- ===============================================================================
-- Verification Queries
-- ===============================================================================
-- Run these to test each function:

-- Test 1: GDP Data
-- SELECT main.finsight_ai.get_gdp_data('USA');

-- Test 2: Inflation Data
-- SELECT main.finsight_ai.get_inflation_data('Argentina');

-- Test 3: Unemployment Data
-- SELECT main.finsight_ai.get_unemployment_data('Germany');

-- Test 4: Interest Rate
-- SELECT main.finsight_ai.get_interest_rate('USA');

-- Test 5: Financial News (requires API key as first parameter)
-- SELECT main.finsight_ai.get_financial_news('<your_api_key>', 'Tesla stock', NULL, NULL, 'en', 3);
-- NOTE: In production, AI Gateway will inject the API key from Databricks Secrets

-- List all functions in schema
-- SHOW FUNCTIONS IN main.finsight_ai;

-- ===============================================================================
-- FUNCTION 6: get_regional_news
-- ===============================================================================
-- Get regional news and context using Tavily API
-- Example: SELECT main.finsight_ai.get_regional_news('tavily-key', 'Argentina economy', 5);
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.get_regional_news(
    api_key STRING,
    query STRING,
    max_results INT
)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Search for regional news and context using Tavily API. API key must be provided as first parameter. Example: get_regional_news(api_key, "Argentina economic policy", 5)'
AS $$
import requests
import json
from datetime import datetime

# Validate API key
if not api_key or api_key.strip() == '':
    return json.dumps({
        "error": "Tavily API key required",
        "message": "API key must be provided as first parameter"
    })

if not max_results:
    max_results = 5

try:
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_domains": [],
        "exclude_domains": []
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    
    results = data.get("results", [])
    
    formatted_results = []
    for result in results:
        formatted_results.append({
            "title": result.get("title", ""),
            "content": result.get("content", ""),
            "url": result.get("url", ""),
            "score": result.get("score", 0),
            "published_date": result.get("published_date", "")
        })
    
    return json.dumps({
        "query": query,
        "results": formatted_results,
        "answer": data.get("answer", ""),
        "source": "Tavily API",
        "retrieved_at": datetime.now().isoformat()
    })
    
except requests.exceptions.RequestException as e:
    return json.dumps({
        "error": "API request failed",
        "message": str(e),
        "query": query
    })
$$;

-- ===============================================================================
-- FUNCTION 7: get_stock_prices
-- ===============================================================================
-- Get historical stock prices using Yahoo Finance (free, no API key needed)
-- Example: SELECT main.finsight_ai.get_stock_prices('AAPL', 30);
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.get_stock_prices(
    symbol STRING,
    days INT
)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Get historical stock prices using Yahoo Finance. Returns OHLCV data. Example: get_stock_prices("AAPL", 30) for last 30 days of Apple stock'
AS $$
import requests
import json
from datetime import datetime, timedelta
import time

if not days:
    days = 30

try:
    # Yahoo Finance API endpoint (free, no key needed)
    # Using period1/period2 for date range
    end_time = int(time.time())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        "period1": start_time,
        "period2": end_time,
        "interval": "1d",
        "includePrePost": "false",
        "events": "div,splits"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if "chart" not in data or "result" not in data["chart"]:
        return json.dumps({
            "error": "No data available",
            "symbol": symbol
        })
    
    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    
    # Format price data
    prices = []
    for i in range(len(timestamps)):
        prices.append({
            "date": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d"),
            "open": quote["open"][i],
            "high": quote["high"][i],
            "low": quote["low"][i],
            "close": quote["close"][i],
            "volume": quote["volume"][i]
        })
    
    # Get metadata
    meta = result["meta"]
    
    return json.dumps({
        "symbol": symbol,
        "currency": meta.get("currency", "USD"),
        "exchange": meta.get("exchangeName", ""),
        "current_price": meta.get("regularMarketPrice"),
        "prices": prices,
        "days_requested": days,
        "days_returned": len(prices),
        "source": "Yahoo Finance",
        "retrieved_at": datetime.now().isoformat()
    })
    
except requests.exceptions.RequestException as e:
    return json.dumps({
        "error": "API request failed",
        "message": str(e),
        "symbol": symbol
    })
except Exception as e:
    return json.dumps({
        "error": "Data parsing failed",
        "message": str(e),
        "symbol": symbol
    })
$$;

-- ===============================================================================
-- FUNCTION 8: get_technical_indicators
-- ===============================================================================
-- Get technical indicators (RSI, MACD, etc.) using Alpha Vantage
-- Example: SELECT main.finsight_ai.get_technical_indicators('alpha-key', 'AAPL', 'RSI');
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.get_technical_indicators(
    api_key STRING,
    symbol STRING,
    indicator STRING
)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Get technical indicators (RSI, MACD, SMA, EMA) using Alpha Vantage API. Supported indicators: RSI, MACD, SMA, EMA. Example: get_technical_indicators(api_key, "AAPL", "RSI")'
AS $$
import requests
import json
from datetime import datetime

if not api_key or api_key.strip() == '':
    return json.dumps({
        "error": "Alpha Vantage API key required",
        "message": "API key must be provided as first parameter"
    })

# Map indicator names to Alpha Vantage function names
indicator_map = {
    "rsi": "RSI",
    "macd": "MACD",
    "sma": "SMA",
    "ema": "EMA",
    "bbands": "BBANDS"
}

indicator_func = indicator_map.get(indicator.lower(), indicator.upper())

try:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": indicator_func,
        "symbol": symbol,
        "interval": "daily",
        "time_period": 14,  # Standard period
        "series_type": "close",
        "apikey": api_key
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    # Check for API errors
    if "Error Message" in data:
        return json.dumps({
            "error": "Invalid symbol or request",
            "message": data["Error Message"],
            "symbol": symbol
        })
    
    if "Note" in data:
        return json.dumps({
            "error": "API rate limit",
            "message": data["Note"],
            "symbol": symbol
        })
    
    # Get indicator data key (varies by indicator)
    data_key = None
    for key in data.keys():
        if "Technical Analysis" in key:
            data_key = key
            break
    
    if not data_key:
        return json.dumps({
            "error": "No indicator data available",
            "symbol": symbol,
            "indicator": indicator
        })
    
    indicator_data = data[data_key]
    
    # Get latest 10 data points
    dates = sorted(indicator_data.keys(), reverse=True)[:10]
    values = []
    
    for date in dates:
        values.append({
            "date": date,
            "values": indicator_data[date]
        })
    
    return json.dumps({
        "symbol": symbol,
        "indicator": indicator_func,
        "metadata": data.get("Meta Data", {}),
        "latest_values": values,
        "source": "Alpha Vantage",
        "retrieved_at": datetime.now().isoformat()
    })
    
except requests.exceptions.RequestException as e:
    return json.dumps({
        "error": "API request failed",
        "message": str(e),
        "symbol": symbol
    })
$$;

-- ===============================================================================
-- FUNCTION 9: detect_corporate_events
-- ===============================================================================
-- Detect corporate events (earnings, M&A, etc.) using Alpha Vantage
-- Example: SELECT main.finsight_ai.detect_corporate_events('alpha-key', 'AAPL');
-- ===============================================================================

CREATE OR REPLACE FUNCTION main.finsight_ai.detect_corporate_events(
    api_key STRING,
    symbol STRING
)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Detect upcoming and recent corporate events (earnings, IPOs) using Alpha Vantage. Example: detect_corporate_events(api_key, "AAPL")'
AS $$
import requests
import json
from datetime import datetime, timedelta

if not api_key or api_key.strip() == '':
    return json.dumps({
        "error": "Alpha Vantage API key required",
        "message": "API key must be provided as first parameter"
    })

try:
    # Get earnings calendar
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "EARNINGS_CALENDAR",
        "symbol": symbol,
        "apikey": api_key
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    # Parse CSV response
    text_data = response.text
    
    if "Error Message" in text_data or "Invalid API call" in text_data:
        return json.dumps({
            "error": "Invalid symbol or request",
            "symbol": symbol
        })
    
    if "premium endpoint" in text_data.lower():
        # Fallback: get company overview which includes earnings date
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if not data or "Symbol" not in data:
            return json.dumps({
                "error": "No data available",
                "symbol": symbol
            })
        
        return json.dumps({
            "symbol": symbol,
            "company_name": data.get("Name", ""),
            "sector": data.get("Sector", ""),
            "industry": data.get("Industry", ""),
            "market_cap": data.get("MarketCapitalization", ""),
            "latest_quarter": data.get("LatestQuarter", ""),
            "earnings_date": data.get("QuarterlyEarningsGrowthYOY", "N/A"),
            "source": "Alpha Vantage",
            "note": "Using company overview (earnings calendar requires premium)",
            "retrieved_at": datetime.now().isoformat()
        })
    
    # Parse CSV
    lines = text_data.strip().split('\n')
    if len(lines) < 2:
        return json.dumps({
            "error": "No earnings data available",
            "symbol": symbol
        })
    
    headers = lines[0].split(',')
    events = []
    
    for line in lines[1:6]:  # Get next 5 events
        values = line.split(',')
        if len(values) >= 3:
            events.append({
                "symbol": values[0],
                "report_date": values[1] if len(values) > 1 else "",
                "fiscal_period": values[2] if len(values) > 2 else "",
                "estimate": values[3] if len(values) > 3 else "",
                "currency": values[4] if len(values) > 4 else "USD"
            })
    
    return json.dumps({
        "symbol": symbol,
        "upcoming_events": events,
        "source": "Alpha Vantage",
        "retrieved_at": datetime.now().isoformat()
    })
    
except requests.exceptions.RequestException as e:
    return json.dumps({
        "error": "API request failed",
        "message": str(e),
        "symbol": symbol
    })
$$;

-- ===============================================================================
-- Verification Queries for New Functions
-- ===============================================================================
-- Run these to test each new function:

-- Test 6: Regional News (Tavily)
-- SELECT main.finsight_ai.get_regional_news('<your_tavily_api_key>', 'Argentina economy', 5);

-- Test 7: Stock Prices (Yahoo Finance - No API key needed)
-- SELECT main.finsight_ai.get_stock_prices('AAPL', 30);

-- Test 8: Technical Indicators (Alpha Vantage)
-- SELECT main.finsight_ai.get_technical_indicators('<your_alpha_vantage_key>', 'AAPL', 'RSI');

-- Test 9: Corporate Events (Alpha Vantage)
-- SELECT main.finsight_ai.detect_corporate_events('<your_alpha_vantage_key>', 'TSLA');

-- ===============================================================================
-- End of UC Functions Setup
-- ===============================================================================