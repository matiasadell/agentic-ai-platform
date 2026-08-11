"""
Unity Catalog Functions as LangChain Tools
==========================================

Wrappers para UC Functions registradas en main.finsight_ai que pueden ser
invocadas por LLMs via tool calling.

Funciones disponibles (9 total):

Macro-económicas (World Bank API):
- get_gdp_data: GDP data
- get_inflation_data: Inflation CPI
- get_unemployment_data: Unemployment rate
- get_interest_rate: Interest rates (USA only, placeholder)

Noticias:
- get_financial_news: Financial news search (NewsAPI)
- get_regional_news: Regional economic news and context (Tavily API)

Análisis técnico de acciones:
- get_stock_prices: Historical OHLCV prices (Yahoo Finance)
- get_technical_indicators: RSI, MACD, SMA, EMA indicators (Alpha Vantage)
- detect_corporate_events: Earnings, IPOs, corporate actions (Alpha Vantage)

Uso:
    from src.agents.tools.uc_functions import get_all_uc_tools
    from langchain_databricks import ChatDatabricks
    
    llm = ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")
    tools = get_all_uc_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # El LLM puede invocar las tools automáticamente
    response = llm_with_tools.invoke("What's Argentina's GDP?")
"""

import json
from typing import Optional, List
from langchain_core.tools import tool
from pyspark.sql import SparkSession


def _get_spark() -> SparkSession:
    """Get or create Spark session."""
    return SparkSession.builder.getOrCreate()


@tool
def get_gdp_data(country: str) -> dict:
    """Get GDP (Gross Domestic Product) data for a country from World Bank API.
    
    Returns GDP in current US dollars for the most recent available year.
    Supports major economies including USA, Argentina, China, Germany, Brazil, etc.
    
    Args:
        country: Country name or ISO code (e.g., 'USA', 'United States', 'Argentina', 'ARG')
    
    Returns:
        Dict containing:
        - country: Full country name
        - country_code: ISO 3-letter code
        - gdp_usd: GDP in current US dollars
        - year: Year of the data
        - indicator: Description of the indicator
        - source: Data source (World Bank API)
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if data not available.
    
    Example:
        >>> result = get_gdp_data("Argentina")
        >>> print(f"GDP: ${result['gdp_usd']:,.0f}")
    """
    spark = _get_spark()
    
    # Sanitize country input to prevent SQL injection
    country_safe = country.replace("'", "''")
    
    result = spark.sql(
        f"SELECT main.finsight_ai.get_gdp_data('{country_safe}')"
    ).collect()[0][0]
    
    return json.loads(result)


@tool
def get_inflation_data(country: str) -> dict:
    """Get inflation rate (CPI) data for a country from World Bank API.
    
    Returns consumer price index annual percentage change for the most recent year.
    
    Args:
        country: Country name or ISO code (e.g., 'USA', 'Argentina', 'China')
    
    Returns:
        Dict containing:
        - country: Full country name
        - country_code: ISO 3-letter code
        - inflation_rate: Annual inflation percentage
        - year: Year of the data
        - indicator: Description (Inflation, consumer prices)
        - source: Data source (World Bank API)
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if data not available.
    
    Example:
        >>> result = get_inflation_data("Argentina")
        >>> print(f"Inflation: {result['inflation_rate']:.2f}%")
    """
    spark = _get_spark()
    country_safe = country.replace("'", "''")
    
    result = spark.sql(
        f"SELECT main.finsight_ai.get_inflation_data('{country_safe}')"
    ).collect()[0][0]
    
    return json.loads(result)


@tool
def get_unemployment_data(country: str) -> dict:
    """Get unemployment rate data for a country from World Bank API.
    
    Returns unemployment as percentage of total labor force for the most recent year.
    
    Args:
        country: Country name or ISO code (e.g., 'USA', 'Germany', 'Argentina')
    
    Returns:
        Dict containing:
        - country: Full country name
        - country_code: ISO 3-letter code
        - unemployment_rate: Unemployment percentage
        - year: Year of the data
        - indicator: Description (Unemployment, total)
        - source: Data source (World Bank API)
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if data not available.
    
    Example:
        >>> result = get_unemployment_data("Germany")
        >>> print(f"Unemployment: {result['unemployment_rate']:.1f}%")
    """
    spark = _get_spark()
    country_safe = country.replace("'", "''")
    
    result = spark.sql(
        f"SELECT main.finsight_ai.get_unemployment_data('{country_safe}')"
    ).collect()[0][0]
    
    return json.loads(result)


@tool
def get_interest_rate(country_code: str = "USA") -> dict:
    """Get interest rate data for a country.
    
    Currently only supports USA Federal Funds Effective Rate (placeholder data).
    
    Args:
        country_code: Country ISO code (currently only 'USA' supported, default: 'USA')
    
    Returns:
        Dict containing:
        - country: Country name
        - country_code: ISO code
        - interest_rate: Current interest rate percentage
        - date: Date of the rate
        - indicator: Description (Federal Funds Rate)
        - source: Data source (placeholder)
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if country not supported.
    
    Example:
        >>> result = get_interest_rate("USA")
        >>> print(f"Fed Rate: {result['interest_rate']:.2f}%")
    """
    spark = _get_spark()
    country_code_safe = country_code.replace("'", "''")
    
    result = spark.sql(
        f"SELECT main.finsight_ai.get_interest_rate('{country_code_safe}')"
    ).collect()[0][0]
    
    return json.loads(result)


@tool
def get_financial_news(
    query: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    language: str = "en",
    max_results: int = 5
) -> dict:
    """Search for financial news articles using NewsAPI.
    
    Returns recent news articles matching the search query, sorted by relevancy.
    
    Args:
        query: Search query for financial news (e.g., 'Tesla stock', 'inflation', 'crypto market')
        from_date: Start date in YYYY-MM-DD format (optional, defaults to 7 days ago)
        to_date: End date in YYYY-MM-DD format (optional, defaults to today)
        language: Language code (optional, defaults to 'en')
        max_results: Maximum number of articles to return (default: 5, max: 100)
    
    Returns:
        Dict containing:
        - query: The search query used
        - total_results: Total number of matching articles
        - articles: List of article dicts with title, description, source, url, published_at
        - from_date: Start date used
        - to_date: End date used
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if API key not configured or request fails.
    
    Example:
        >>> result = get_financial_news("Tesla stock", max_results=3)
        >>> for article in result['articles']:
        ...     print(f"{article['title']} - {article['source']}")
    """
    spark = _get_spark()
    
    # Get API key from Databricks Secrets
    try:
        from databricks.sdk.runtime import dbutils
        api_key = dbutils.secrets.get(scope="finsight", key="NEWS_API_KEY")
    except Exception as e:
        return {
            "error": "NewsAPI key not accessible",
            "message": f"Failed to retrieve API key from Databricks Secrets: {str(e)}"
        }
    
    # Sanitize inputs
    query_safe = query.replace("'", "''")
    language_safe = language.replace("'", "''")
    
    # Build SQL query
    from_date_sql = f"'{from_date}'" if from_date else "NULL"
    to_date_sql = f"'{to_date}'" if to_date else "NULL"
    
    result = spark.sql(f"""
        SELECT main.finsight_ai.get_financial_news(
            '{api_key}',
            '{query_safe}',
            {from_date_sql},
            {to_date_sql},
            '{language_safe}',
            {max_results}
        )
    """).collect()[0][0]
    
    return json.loads(result)




# ============================================================================
# NEW TOOLS - Phase 2 Workers
# ============================================================================

@tool
def get_regional_news(
    query: str,
    max_results: int = 5
) -> dict:
    """Search for regional news and economic context using Tavily API.
    
    Tavily provides comprehensive web search with context summarization,
    ideal for regional economic analysis and news aggregation.
    
    Args:
        query: Search query (e.g., 'Argentina economic policy', 'Brazil inflation')
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        Dict containing:
        - query: The search query used
        - results: List of result dicts with title, content, url, score, published_date
        - answer: AI-generated summary answer from Tavily
        - source: Data source (Tavily API)
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if API key not configured or request fails.
    
    Example:
        >>> result = get_regional_news("Argentina central bank policy", max_results=3)
        >>> print(result['answer'])  # Summary
        >>> for r in result['results']:
        ...     print(f"{r['title']}: {r['url']}")
    """
    spark = _get_spark()
    
    # Get API key from Databricks Secrets
    try:
        from databricks.sdk.runtime import dbutils
        api_key = dbutils.secrets.get(scope="finsight", key="tavily-api-key")
    except Exception as e:
        return {
            "error": "Tavily API key not accessible",
            "message": f"Failed to retrieve API key from Databricks Secrets: {str(e)}"
        }
    
    # Sanitize inputs
    query_safe = query.replace("'", "''")
    
    result = spark.sql(f"""
        SELECT main.finsight_ai.get_regional_news(
            '{api_key}',
            '{query_safe}',
            {max_results}
        )
    """).collect()[0][0]
    
    return json.loads(result)


@tool
def get_stock_prices(
    symbol: str,
    days: int = 30
) -> dict:
    """Get historical stock prices using Yahoo Finance.
    
    Returns OHLCV (Open, High, Low, Close, Volume) data for the specified period.
    Free API, no authentication required.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'GGAL.BA' for ADRs)
        days: Number of historical days to retrieve (default: 30)
    
    Returns:
        Dict containing:
        - symbol: Stock ticker
        - currency: Price currency (usually USD)
        - exchange: Exchange name
        - current_price: Most recent price
        - prices: List of OHLCV data points with date, open, high, low, close, volume
        - days_requested: Number of days requested
        - days_returned: Actual number of days returned
        - source: Data source (Yahoo Finance)
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if symbol not found or request fails.
    
    Example:
        >>> result = get_stock_prices("AAPL", days=7)
        >>> for price in result['prices']:
        ...     print(f"{price['date']}: ${price['close']:.2f}")
    """
    spark = _get_spark()
    symbol_safe = symbol.replace("'", "''")
    
    result = spark.sql(f"""
        SELECT main.finsight_ai.get_stock_prices(
            '{symbol_safe}',
            {days}
        )
    """).collect()[0][0]
    
    return json.loads(result)


@tool
def get_technical_indicators(
    symbol: str,
    indicator: str = "RSI"
) -> dict:
    """Get technical indicators (RSI, MACD, SMA, EMA) using Alpha Vantage.
    
    Calculates common technical analysis indicators for stocks.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        indicator: Indicator type - 'RSI', 'MACD', 'SMA', 'EMA', 'BBANDS' (default: 'RSI')
    
    Returns:
        Dict containing:
        - symbol: Stock ticker
        - indicator: Indicator name
        - metadata: Indicator metadata (period, series type, etc.)
        - latest_values: List of recent indicator values with dates
        - source: Data source (Alpha Vantage)
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if symbol invalid, rate limit hit, or request fails.
    
    Example:
        >>> result = get_technical_indicators("AAPL", "RSI")
        >>> latest = result['latest_values'][0]
        >>> print(f"RSI: {latest['values']['RSI']}")
    """
    spark = _get_spark()
    
    # Get API key from Databricks Secrets
    try:
        from databricks.sdk.runtime import dbutils
        api_key = dbutils.secrets.get(scope="finsight", key="alpha-vantage-api-key")
    except Exception as e:
        return {
            "error": "Alpha Vantage API key not accessible",
            "message": f"Failed to retrieve API key from Databricks Secrets: {str(e)}"
        }
    
    symbol_safe = symbol.replace("'", "''")
    indicator_safe = indicator.replace("'", "''")
    
    result = spark.sql(f"""
        SELECT main.finsight_ai.get_technical_indicators(
            '{api_key}',
            '{symbol_safe}',
            '{indicator_safe}'
        )
    """).collect()[0][0]
    
    return json.loads(result)


@tool
def detect_corporate_events(
    symbol: str
) -> dict:
    """Detect upcoming and recent corporate events using Alpha Vantage.
    
    Identifies earnings dates, corporate actions, and other material events.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict containing:
        - symbol: Stock ticker
        - company_name: Full company name (if available)
        - sector: Company sector
        - industry: Company industry
        - upcoming_events: List of upcoming earnings/events with dates
        - latest_quarter: Most recent quarter reported
        - source: Data source (Alpha Vantage)
        - retrieved_at: Timestamp of retrieval
        
        Or error dict if symbol invalid or request fails.
    
    Example:
        >>> result = detect_corporate_events("AAPL")
        >>> for event in result['upcoming_events']:
        ...     print(f"{event['report_date']}: {event['fiscal_period']}")
    """
    spark = _get_spark()
    
    # Get API key from Databricks Secrets
    try:
        from databricks.sdk.runtime import dbutils
        api_key = dbutils.secrets.get(scope="finsight", key="alpha-vantage-api-key")
    except Exception as e:
        return {
            "error": "Alpha Vantage API key not accessible",
            "message": f"Failed to retrieve API key from Databricks Secrets: {str(e)}"
        }
    
    symbol_safe = symbol.replace("'", "''")
    
    result = spark.sql(f"""
        SELECT main.finsight_ai.detect_corporate_events(
            '{api_key}',
            '{symbol_safe}'
        )
    """).collect()[0][0]
    
    return json.loads(result)

# ============================================================================
# Tool Grouping Functions (Updated with Phase 2 Tools)
# ============================================================================

def get_all_uc_tools() -> List:
    """Get ALL UC Function tools for binding to an LLM (9 total).
    
    Includes macro-economic data, news, and technical stock analysis tools.
    
    Returns:
        List of LangChain tool objects that can be bound to an LLM.
    
    Example:
        >>> from langchain_databricks import ChatDatabricks
        >>> from src.agents.tools.uc_functions import get_all_uc_tools
        >>> 
        >>> llm = ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")
        >>> tools = get_all_uc_tools()
        >>> llm_with_tools = llm.bind_tools(tools)
        >>> 
        >>> response = llm_with_tools.invoke("What's the GDP of Argentina?")
    """
    return [
        # Macro-economic tools (4)
        get_gdp_data,
        get_inflation_data,
        get_unemployment_data,
        get_interest_rate,
        # News tools (2)
        get_financial_news,
        get_regional_news,
        # Technical analysis tools (3)
        get_stock_prices,
        get_technical_indicators,
        detect_corporate_events
    ]


def get_macro_tools() -> List:
    """Get only macroeconomic data tools (no news or technical analysis).
    
    Returns:
        List of macro-focused tools (4 tools).
    """
    return [
        get_gdp_data,
        get_inflation_data,
        get_unemployment_data,
        get_interest_rate
    ]


def get_news_tools() -> List:
    """Get only news-related tools (2 tools).
    
    Includes both financial news (NewsAPI) and regional economic news (Tavily).
    
    Returns:
        List of news-focused tools.
    """
    return [
        get_financial_news,
        get_regional_news
    ]


def get_technical_tools() -> List:
    """Get only technical stock analysis tools (3 tools).
    
    Includes stock prices, technical indicators, and corporate event detection.
    Ideal for IndicatorAnalysisWorker and EventDetectionWorker.
    
    Returns:
        List of technical analysis tools.
    """
    return [
        get_stock_prices,
        get_technical_indicators,
        detect_corporate_events
    ]
