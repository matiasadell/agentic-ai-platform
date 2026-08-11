# 🏗️ Arquitectura Multi-Agent Jerárquica

## 📋 Índice
1. [Cambio de Paradigma](#cambio-de-paradigma)
2. [Arquitectura Anterior vs Nueva](#arquitectura-anterior-vs-nueva)
3. [Componentes Principales](#componentes-principales)
4. [Patrón ReAct](#patrón-react)
5. [Flujo de Ejecución](#flujo-de-ejecución)
6. [Cómo Extender](#cómo-extender)

---

## 🎯 Cambio de Paradigma

### ❌ Arquitectura Anterior (Workers)

```python
class FinancialStatementWorker:
    def analyze_statements(self, ticker, query):
        # Solo HTTP call
        response = requests.get(API_URL)
        return {"data": response.json()}
```

**Problemas:**
- Workers eran solo **funciones de datos** (data fetchers)
- No razonamiento, no LLM
- Supervisor orquestaba **funciones simples**
- NO era arquitectura multi-agent verdadera

### ✅ Nueva Arquitectura (Agents)

```python
@tool
def fetch_financial_statements(ticker: str) -> str:
    # LangChain tool wraps API call
    response = requests.get(API_URL)
    return formatted_data

agent = create_react_agent(
    model=llm,                    # Tiene su propio LLM
    tools=[fetch_financial_statements],  # Usa tools
    prompt="You are a financial analyst..."  # Puede razonar
)
```

**Beneficios:**
- Agents son **agentes inteligentes** con LLM
- Pueden **razonar sobre los datos** (ReAct pattern)
- Supervisor coordina **agents autónomos**
- **Verdadera arquitectura multi-agent jerárquica**

---

## 📊 Arquitectura Anterior vs Nueva

| Aspecto | Workers (❌ Anterior) | Agents (✅ Nueva) |
|---------|----------------------|-------------------|
| **Definición** | Clases Python simples | `create_react_agent` con LLM |
| **Razonamiento** | ❌ No (solo HTTP call) | ✅ Sí (ReAct pattern) |
| **LLM** | ❌ No tiene | ✅ Cada agent tiene su propio LLM |
| **Tools** | ❌ No usa tools | ✅ Tools de LangChain |
| **Iteración** | ❌ Ejecuta una vez | ✅ Puede iterar y refinar |
| **Supervisor** | StateGraph manual | StateGraph coordinando agents |
| **Tipo** | Data fetchers | Agents inteligentes |

---

## 🧩 Componentes Principales

### 1. **Agents (fundamental_agents.py)**

Cada agent es un `create_react_agent` con:
- **Su propio LLM** → Puede razonar
- **Tools específicas** → Wrappean APIs
- **Prompt especializado** → Define su rol

```python
# Example: Financial Statement Agent
agent = create_react_agent(
    model=llm,
    tools=[fetch_financial_statements],  # LangChain tool
    prompt=(
        "You are a financial statement analyst.\\n"
        "Analyze balance sheets, income statements, cash flow.\\n"
        "Use fetch_financial_statements tool to get data.\\n"
        "Provide clear analysis of financial health."
    ),
    name="financial_statement_agent"
)
```

**4 Fundamental Agents:**
1. `financial_statement_agent` → Analiza estados financieros
2. `key_ratios_agent` → Calcula ratios (P/E, ROE, etc.)
3. `earnings_agent` → Analiza earnings y EPS
4. `valuation_agent` → Estima valoración (DCF)

### 2. **Tools (LangChain Tools)**

Cada tool es un wrapper de API que:
- Hace la llamada HTTP
- Formatea la respuesta
- Retorna string interpretable por el LLM

```python
@tool
def fetch_financial_statements(ticker: str) -> str:
    """Fetch financial statements from Alpha Vantage."""
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    response = requests.get(API_URL, params={'symbol': ticker, 'apikey': api_key})
    data = response.json()
    
    # Format for LLM
    return f"""
    Financial Statements for {ticker}:
    - Revenue: ${data['revenue']}
    - Net Income: ${data['net_income']}
    - Free Cash Flow: ${data['fcf']}
    """
```

**4 Fundamental Tools:**
- `fetch_financial_statements` → Alpha Vantage API
- `fetch_key_ratios` → Financial Modeling Prep API
- `fetch_earnings_data` → Financial Modeling Prep API
- `calculate_valuation` → In-house DCF model

### 3. **Supervisor (fundamental_supervisor_v2.py)**

El supervisor coordina agents usando **StateGraph**:

```python
workflow = StateGraph(MessagesState)

# Add agents as nodes
workflow.add_node("financial_agent", financial_agent_node)
workflow.add_node("ratios_agent", ratios_agent_node)
workflow.add_node("earnings_agent", earnings_agent_node)
workflow.add_node("valuation_agent", valuation_agent_node)

# Sequential execution
workflow.add_edge(START, "financial_agent")
workflow.add_edge("financial_agent", "ratios_agent")
workflow.add_edge("ratios_agent", "earnings_agent")
workflow.add_edge("earnings_agent", "valuation_agent")
workflow.add_edge("valuation_agent", END)
```

**Flow:**
```
START → financial_agent → ratios_agent → earnings_agent → valuation_agent → END
```

---

## 🔁 Patrón ReAct

### ¿Qué es ReAct?

**Re**asoning + **Act**ing = **ReAct**

Un agent ReAct **alterna entre razonamiento y acción**:

```
User Query: "Analyze Apple financial health"

Agent Reasoning (Thought):
"I need to get Apple's financial statements first"

Agent Action:
Uses tool: fetch_financial_statements(ticker="AAPL")

Tool Response:
"Revenue: $394B, Net Income: $97B, FCF: $111B"

Agent Reasoning (Thought):
"Strong financials. Now I'll interpret this data..."

Agent Final Answer:
"Apple shows excellent financial health with:
- Strong revenue of $394B
- High profitability: $97B net income
- Robust cash generation: $111B FCF
This indicates a financially stable company."
```

### Ventajas del ReAct Pattern:

1. **Iteración inteligente** → Agent puede llamar múltiples tools
2. **Razonamiento explícito** → Podemos ver su proceso de pensamiento
3. **Auto-corrección** → Puede refinar su análisis
4. **Flexibilidad** → No está limitado a una sola llamada API

---

## 🔄 Flujo de Ejecución

### Ejemplo: "Analyze Tesla fundamentals"

```
1. User Query
   ↓
2. Supervisor recibe query
   ↓
3. financial_agent invocado
   ├─ Thought: "I need Tesla's financial statements"
   ├─ Action: fetch_financial_statements("TSLA")
   ├─ Response: "Revenue: $96B, Net Income: $15B..."
   └─ Analysis: "Strong revenue growth..."
   ↓
4. ratios_agent invocado
   ├─ Thought: "I need Tesla's key ratios"
   ├─ Action: fetch_key_ratios("TSLA")
   ├─ Response: "P/E: 60, ROE: 28%..."
   └─ Analysis: "High valuation multiples..."
   ↓
5. earnings_agent invocado
   ├─ Thought: "I need Tesla's earnings data"
   ├─ Action: fetch_earnings_data("TSLA")
   ├─ Response: "EPS Beat by 15%..."
   └─ Analysis: "Consistently beating estimates..."
   ↓
6. valuation_agent invocado
   ├─ Thought: "I'll estimate Tesla's fair value"
   ├─ Action: calculate_valuation(revenue=96B, fcf=15B)
   ├─ Response: "DCF EV: $800B..."
   └─ Analysis: "Currently trading at premium..."
   ↓
7. Supervisor retorna análisis completo
```

---

## 🔧 Cómo Extender

### Crear Nuevos Agents (Ejemplo: Macro Domain)

#### 1. Crear Tools (`macro_agents.py`)

```python
from langchain_core.tools import tool

@tool
def fetch_macro_indicators(country: str) -> str:
    """Fetch macro indicators from FRED API."""
    # API call to FRED
    response = requests.get(FRED_URL)
    return formatted_indicators

@tool
def fetch_regional_context(region: str) -> str:
    """Fetch regional economic context."""
    # API call
    return formatted_context
```

#### 2. Crear Agents

```python
from langgraph.prebuilt import create_react_agent

def create_macro_data_agent(llm=None):
    if llm is None:
        llm = init_chat_model("openai:gpt-4o-mini")
    
    agent = create_react_agent(
        model=llm,
        tools=[fetch_macro_indicators],
        prompt=(
            "You are a macro economist agent.\\n"
            "Analyze GDP, inflation, unemployment data.\\n"
            "Use fetch_macro_indicators tool."
        ),
        name="macro_data_agent"
    )
    return agent
```

#### 3. Crear Supervisor

```python
from langgraph.graph import StateGraph, MessagesState, START, END

def create_macro_supervisor(llm=None):
    if llm is None:
        llm = init_chat_model("openai:gpt-4o-mini")
    
    # Create agents
    macro_agent = create_macro_data_agent(llm)
    regional_agent = create_regional_context_agent(llm)
    
    # Build graph
    workflow = StateGraph(MessagesState)
    
    workflow.add_node("macro_agent", lambda s: macro_agent.invoke(s))
    workflow.add_node("regional_agent", lambda s: regional_agent.invoke(s))
    
    workflow.add_edge(START, "macro_agent")
    workflow.add_edge("macro_agent", "regional_agent")
    workflow.add_edge("regional_agent", END)
    
    return workflow.compile()
```

---

## 📁 Estructura de Archivos

```
agentic-ai-platform/
├── src/
│   ├── agents/
│   │   ├── fundamental_agents.py      # ✅ Agents + Tools
│   │   ├── macro_agents.py            # 🔜 TO-DO
│   │   ├── news_agents.py             # 🔜 TO-DO
│   │   └── supervisors/
│   │       ├── fundamental_supervisor_v2.py   # ✅ Supervisor
│   │       ├── macro_supervisor_v2.py         # 🔜 TO-DO
│   │       └── news_supervisor_v2.py          # 🔜 TO-DO
│   ├── workers/                       # ❌ DEPRECATED
│   │   └── fundamental.py             # Old worker classes
│   └── utils/
│       └── config.py
├── validate_all_workers_api.ipynb     # ✅ Validation notebook
└── ARCHITECTURE.md                    # ✅ This file
```

---

## ✅ Status Actual

### Completado:
- ✅ **fundamental_agents.py** → 4 agents + 4 tools
- ✅ **fundamental_supervisor_v2.py** → Supervisor with StateGraph
- ✅ **validate_all_workers_api** → Updated notebook with agent tests

### Pendiente:
- 🔜 **macro_agents.py** → Convertir macro workers a agents
- 🔜 **news_agents.py** → Convertir news workers a agents
- 🔜 **Master orchestrator** → Top-level supervisor coordinando fundamental + macro + news

---

## 🎯 Diferencia Clave

**Workers = Data fetchers** (fetch data, return dict)  
**Agents = Intelligent analysts** (fetch data, **reason**, interpret, provide insights)

La nueva arquitectura permite que cada componente **piense** sobre los datos, no solo obtenerlos.

---

## 📚 Referencias

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **ReAct Paper**: https://arxiv.org/abs/2210.03629
- **8-multiagent notebook**: Patrón de referencia usado

---

**Última actualización:** 2026-07-30
