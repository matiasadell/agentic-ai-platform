"""
Macro Data Worker Agent
======================

Agente especializado en análisis macroeconómico que utiliza UC Functions
como tools para obtener datos en tiempo real.

Ejemplo de uso:
    worker = MacroDataWorker()
    response = worker.analyze_economy("Argentina")
    print(response)

UC Functions utilizadas (via LangChain tool calling):
- get_gdp_data: GDP data del World Bank
- get_inflation_data: Inflación (CPI) del World Bank  
- get_unemployment_data: Desempleo del World Bank
- get_interest_rate: Tasas de interés (USA placeholder)
"""

from databricks_langchain import ChatDatabricks
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any, List
import json

# Importar las UC Function tools
from src.agents.tools.uc_functions import get_macro_tools


class MacroDataWorker:
    """
    Worker agent que analiza indicadores macroeconómicos usando UC Functions.
    
    Arquitectura:
    1. LLM (via AI Gateway) recibe la consulta del usuario
    2. LLM decide qué tools invocar (get_gdp_data, get_inflation_data, etc.)
    3. Las tools llaman a UC Functions vía Spark SQL
    4. UC Functions ejecutan Python y llaman APIs externas
    5. Resultados regresan al LLM para generar respuesta
    """
    
    def __init__(self, endpoint: str = "databricks-meta-llama-3-3-70b-instruct"):
        """
        Inicializa el worker con acceso a UC Functions tools.
        
        Args:
            endpoint: Model serving endpoint (default: databricks-meta-llama-3-3-70b-instruct)
                     TODO: Cambiar a ai-gateway:/main.finsight_ai.finsight-chat cuando esté funcionando
        """
        # LLM con AI Gateway
        self.llm = ChatDatabricks(
            endpoint=endpoint,
            temperature=0.1,  # Respuestas consistentes para datos numéricos
            max_tokens=2000
        )
        
        # Obtener tools de UC Functions (CLAVE: así se conectan las tools)
        self.tools = get_macro_tools()  # [get_gdp_data, get_inflation_data, ...]
        
        # Bind tools al LLM (tool calling automático)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # System prompt para el agente
        self.system_prompt = """Eres un analista macroeconómico experto. 
        
Usas datos en tiempo real del World Bank API a través de UC Functions.

Cuando el usuario pregunta sobre un país:
1. Usa get_gdp_data para obtener el GDP
2. Usa get_inflation_data para obtener la inflación
3. Usa get_unemployment_data para obtener el desempleo
4. Usa get_interest_rate si es USA

Analiza los datos y proporciona insights claros y concisos.
Siempre incluye los valores numéricos y el año de los datos.
"""
    
    def analyze_economy(self, country: str) -> Dict[str, Any]:
        """
        Analiza la economía de un país usando UC Functions tools.
        
        El LLM automáticamente:
        1. Decide qué tools llamar (get_gdp_data, get_inflation_data, etc.)
        2. Ejecuta las tools
        3. Recibe los resultados
        4. Genera análisis
        
        Args:
            country: Nombre del país (ej: "Argentina", "USA")
            
        Returns:
            Dict[str, Any] compatible con MacroResponse schema:
            {
                "success": bool,
                "worker_name": str,
                "query": str,
                "indicators": List[Dict],
                "trend": Optional[str],
                "summary": str,
                "data_source": str,
                "indicators_count": int
            }
            
        Example:
            >>> worker = MacroDataWorker()
            >>> result = worker.analyze_economy("Argentina")
            >>> print(result["summary"])
        """
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Analiza la situación macroeconómica de {country}. Dame GDP, inflación y desempleo.")
            ]
            
            # TOOL CALLING AUTOMÁTICO:
            # El LLM ve las tools disponibles y las invoca según sea necesario
            response = self.llm_with_tools.invoke(messages)
            
            # Recopilar indicators data
            indicators = []
            tool_results = []
            
            # Si el LLM invocó tools, ejecutarlas y obtener resultados
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    # Encontrar la tool y ejecutarla
                    for tool in self.tools:
                        if tool.name == tool_name:
                            result = tool.invoke(tool_args)
                            tool_results.append({
                                'tool': tool_name,
                                'result': result
                            })
                            
                            # Parsear result como indicator
                            try:
                                result_data = json.loads(result) if isinstance(result, str) else result
                                indicators.append({
                                    'name': tool_name.replace('get_', '').replace('_data', ''),
                                    'value': result_data.get('value') or result_data.get('gdp_usd') or result_data.get('inflation_rate') or result_data.get('unemployment_rate'),
                                    'year': result_data.get('year'),
                                    'source': tool_name
                                })
                            except:
                                pass
                            
                            break
                
                # Segunda llamada al LLM con los resultados de las tools
                messages.append(response)
                messages.append(HumanMessage(
                    content=f"Tool results: {json.dumps(tool_results, indent=2)}"
                ))
                
                final_response = self.llm.invoke(messages)
                analysis_text = final_response.content
            else:
                # Si no hubo tool calls, usar respuesta directa
                analysis_text = response.content
            
            # Determinar trend basado en análisis
            trend = "neutral"
            analysis_lower = analysis_text.lower()
            if any(word in analysis_lower for word in ["positive", "growth", "improving", "strong"]):
                trend = "bullish"
            elif any(word in analysis_lower for word in ["negative", "declining", "weak", "recession"]):
                trend = "bearish"
            
            # Retornar dict estructurado compatible con MacroResponse
            return {
                "success": True,
                "worker_name": "MacroDataWorker",
                "query": country,
                "indicators": indicators,
                "trend": trend,
                "summary": analysis_text,
                "data_source": "World Bank API via UC Functions",
                "indicators_count": len(indicators),
                "time_range": "latest available"
            }
        
        except Exception as e:
            # En caso de error, retornar error response válido
            return {
                "success": False,
                "worker_name": "MacroDataWorker",
                "query": country,
                "indicators": [],
                "indicators_count": 0,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def compare_countries(self, countries: List[str]) -> Dict[str, Any]:
        """
        Compara indicadores macroeconómicos entre múltiples países.
        
        Args:
            countries: Lista de países a comparar
            
        Returns:
            Dict[str, Any] compatible con MacroResponse schema
            
        Example:
            >>> result = worker.compare_countries(["Argentina", "Brazil", "USA"])
            >>> print(result["summary"])
        """
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(
                    content=f"Compara los indicadores macroeconómicos (GDP, inflación, desempleo) de estos países: {', '.join(countries)}"
                )
            ]
            
            response = self.llm_with_tools.invoke(messages)
            
            indicators = []
            tool_results = []
            
            # Procesar tool calls (mismo patrón que analyze_economy)
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    for tool in self.tools:
                        if tool.name == tool_name:
                            result = tool.invoke(tool_args)
                            tool_results.append({
                                'tool': tool_name,
                                'args': tool_args,
                                'result': result
                            })
                            
                            # Parsear result como indicator
                            try:
                                result_data = json.loads(result) if isinstance(result, str) else result
                                country_name = tool_args.get('country_code', 'Unknown')
                                indicators.append({
                                    'name': tool_name.replace('get_', '').replace('_data', ''),
                                    'value': result_data.get('value') or result_data.get('gdp_usd') or result_data.get('inflation_rate') or result_data.get('unemployment_rate'),
                                    'year': result_data.get('year'),
                                    'country': country_name,
                                    'source': tool_name
                                })
                            except:
                                pass
                            
                            break
                
                messages.append(response)
                messages.append(HumanMessage(
                    content=f"Datos obtenidos: {json.dumps(tool_results, indent=2)}"
                ))
                
                final_response = self.llm.invoke(messages)
                analysis_text = final_response.content
            else:
                analysis_text = response.content
            
            return {
                "success": True,
                "worker_name": "MacroDataWorker",
                "query": f"Comparison: {', '.join(countries)}",
                "indicators": indicators,
                "trend": "comparative",
                "summary": analysis_text,
                "data_source": "World Bank API via UC Functions",
                "indicators_count": len(indicators),
                "time_range": "latest available"
            }
        
        except Exception as e:
            return {
                "success": False,
                "worker_name": "MacroDataWorker",
                "query": f"Comparison: {', '.join(countries)}",
                "indicators": [],
                "indicators_count": 0,
                "error": str(e),
                "error_type": type(e).__name__
            }


# ============================================================================
# EJEMPLO DE USO DIRECTO (sin LangChain tool calling)
# ============================================================================

def direct_uc_function_call_example():
    """
    Si NO quieres usar LangChain tool calling, puedes llamar UC Functions
    directamente vía Spark SQL.
    
    Este approach es útil cuando:
    - Necesitas control exacto de cuándo llamar cada función
    - No quieres que el LLM decida qué tools usar
    - Prefieres lógica imperativa vs agéntica
    """
    from pyspark.sql import SparkSession
    import json
    
    spark = SparkSession.builder.getOrCreate()
    
    # Llamada directa a UC Function
    result = spark.sql("""
        SELECT main.finsight_ai.get_gdp_data('Argentina')
    """).collect()[0][0]
    
    data = json.loads(result)
    print(f"GDP de Argentina: ${data['gdp_usd']:,.0f} ({data['year']})")
    
    return data


# ============================================================================
# EJEMPLO CON LANGGRAPH (Agente con state machine)
# ============================================================================

from typing import TypedDict, Annotated
# Commented out - not needed for current supervisor usage
# from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolNode

# Commented out - not needed for current supervisor usage
# class AgentState(TypedDict):
#     """Estado del agente."""
#     messages: List[Any]
#     country: str
#     gdp_data: Dict[str, Any]
#     inflation_data: Dict[str, Any]
#     unemployment_data: Dict[str, Any]


# def create_macro_agent_with_langgraph() -> StateGraph:
#     """
#     Crea un agente más sofisticado usando LangGraph con state machine.
#     
#     Este approach es útil cuando:
#     - Necesitas un flujo de trabajo multi-step
#     - Quieres controlar el orden de ejecución
#     - Necesitas mantener estado entre llamadas
#     """
#     # Crear tools node
#     tools = get_macro_tools()
#     tool_node = ToolNode(tools)
#     
#     # LLM con tools
#     llm = ChatDatabricks(endpoint="ai-gateway:/main.finsight_ai.finsight-chat")
#     llm_with_tools = llm.bind_tools(tools)
#     
#     def call_model(state: AgentState):
#         """Nodo que llama al LLM."""
#         response = llm_with_tools.invoke(state["messages"])
#         return {"messages": state["messages"] + [response]}
#     
#     def should_continue(state: AgentState):
#         """Decide si continuar con tools o terminar."""
#         last_message = state["messages"][-1]
#         if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
#             return "continue"
#         return "end"
#     
#     # Construir el grafo
#     workflow = StateGraph(AgentState)
#     
#     workflow.add_node("agent", call_model)
#     workflow.add_node("tools", tool_node)
#     
#     workflow.set_entry_point("agent")
#     
#     workflow.add_conditional_edges(
#         "agent",
#         should_continue,
#         {
#             "continue": "tools",
#             "end": END
#         }
#     )
#     
#     workflow.add_edge("tools", "agent")
#     
#     return workflow.compile()


if __name__ == "__main__":
    # Ejemplo 1: Worker simple
    print("=" * 80)
    print("EJEMPLO 1: MacroDataWorker")
    print("=" * 80)
    
    worker = MacroDataWorker()
    result = worker.analyze_economy("Argentina")
    print(result)
    
    # Ejemplo 2: Comparación de países
    print("\n" + "=" * 80)
    print("EJEMPLO 2: Comparación de países")
    print("=" * 80)
    
    comparison = worker.compare_countries(["Argentina", "Brazil", "USA"])
    print(comparison)
    
    # Ejemplo 3: Llamada directa
    print("\n" + "=" * 80)
    print("EJEMPLO 3: Llamada directa a UC Function")
    print("=" * 80)
    
    data = direct_uc_function_call_example()
    print(json.dumps(data, indent=2))