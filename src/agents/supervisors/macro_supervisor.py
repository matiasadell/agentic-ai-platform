"""
Macro Supervisor (Nivel 2)
===========================

Supervisor que coordina los 3 workers de análisis macroeconómico:
- MacroDataWorker: Datos macro (GDP, inflation, unemployment, interest rates)
- RegionalContextWorker: Contexto regional y noticias económicas
- IndicatorAnalysisWorker: Análisis técnico de stocks (prices, indicators)

Arquitectura de 3 Niveles:
  Nivel 1: Strategic Orchestrator (pendiente)
           ↓
  Nivel 2: MacroSupervisor (✅ Este supervisor)
           ↓
  Nivel 3: Workers (3 workers)
           ├─ MacroDataWorker
           ├─ RegionalContextWorker
           └─ IndicatorAnalysisWorker

Capacidades:
- Routing inteligente con LLM (decide qué workers invocar)
- Ejecución paralela de workers
- Síntesis de resultados de múltiples workers
- Error handling y retries
- Observabilidad completa

Uso:
    from src.agents.supervisors.macro_supervisor import MacroSupervisor
    
    supervisor = MacroSupervisor()
    result = supervisor.process("What is the GDP of USA and Argentina?")
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from databricks_langchain import ChatDatabricks
from langchain_core.messages import HumanMessage, SystemMessage


class MacroSupervisor:
    """
    Supervisor de Nivel 2 para análisis macroeconómico.
    
    Coordina 3 workers especializados usando routing inteligente con LLM.
    """
    
    def __init__(self):
        """Initialize MacroSupervisor con LLM y workers."""
        
        # LLM para routing y síntesis
        self.llm = ChatDatabricks(
            endpoint="databricks-meta-llama-3-3-70b-instruct",
            temperature=0.1
        )
        
        # Lazy initialization de workers
        self._workers = {}
        self._worker_descriptions = {
            "MacroDataWorker": {
                "description": "Retrieves macroeconomic data: GDP, inflation, unemployment, interest rates",
                "keywords": ["gdp", "inflation", "unemployment", "interest rate", "macro", "economic data"],
                "capabilities": ["World Bank API data", "FRED economic indicators", "Multi-country comparisons"]
            },
            "RegionalContextWorker": {
                "description": "Analyzes regional economic context, news, and policy changes",
                "keywords": ["region", "country", "economy", "news", "policy", "context", "latin america"],
                "capabilities": ["Regional news search", "Economic context analysis", "Policy impact assessment"]
            },
            "IndicatorAnalysisWorker": {
                "description": "Analyzes stock prices and technical indicators (RSI, MACD, SMA, etc.)",
                "keywords": ["stock", "ticker", "rsi", "macd", "sma", "ema", "technical", "indicator", "price"],
                "capabilities": ["Historical stock prices", "Technical indicators (RSI, MACD)", "Price trend analysis"]
            }
        }
    
    def _get_worker(self, worker_name: str):
        """Lazy load worker (evita circular imports y mejora performance)."""
        if worker_name not in self._workers:
            if worker_name == "MacroDataWorker":
                from src.agents.workers.macro_data_worker import MacroDataWorker
                self._workers[worker_name] = MacroDataWorker()
            elif worker_name == "RegionalContextWorker":
                from src.agents.workers.regional_context_worker import RegionalContextWorker
                self._workers[worker_name] = RegionalContextWorker()
            elif worker_name == "IndicatorAnalysisWorker":
                from src.agents.workers.indicator_analysis_worker import IndicatorAnalysisWorker
                self._workers[worker_name] = IndicatorAnalysisWorker()
            else:
                raise ValueError(f"Unknown worker: {worker_name}")
        
        return self._workers[worker_name]
    
    def _route_query(self, query: str) -> Dict[str, Any]:
        """
        Usa LLM para decidir qué workers invocar.
        
        Args:
            query: User query
        
        Returns:
            Dict con:
            - workers: List[str] - Nombres de workers a invocar
            - reasoning: str - Explicación del routing
        """
        print(f"\n🧠 Routing query with LLM...")
        
        # Construir prompt de routing
        worker_info = "\n".join([
            f"- {name}: {info['description']}\n  Keywords: {', '.join(info['keywords'])}\n  Capabilities: {', '.join(info['capabilities'])}"
            for name, info in self._worker_descriptions.items()
        ])
        
        routing_prompt = f"""
You are a routing agent for a macroeconomic analysis system. 

Available workers:
{worker_info}

User query: "{query}"

Your task:
1. Analyze the query and determine which worker(s) should handle it
2. Select 1-3 workers based on the query requirements
3. Provide clear reasoning for your selection

Respond ONLY with valid JSON in this exact format:
{{
  "workers": ["WorkerName1", "WorkerName2"],
  "reasoning": "Brief explanation of why these workers were selected"
}}

Rules:
- Use EXACT worker names from the list above
- Select minimum necessary workers (prefer 1 if possible)
- For simple queries, use only 1 worker
- For complex queries combining multiple topics, use 2-3 workers
- Always return valid JSON
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=routing_prompt)])
            
            # Parse LLM response
            content = response.content.strip()
            
            # Try to extract JSON (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            routing_decision = json.loads(content)
            
            # Validate
            if "workers" not in routing_decision or not isinstance(routing_decision["workers"], list):
                raise ValueError("Invalid routing response: missing 'workers' list")
            
            # Validate worker names
            valid_workers = [w for w in routing_decision["workers"] if w in self._worker_descriptions]
            if not valid_workers:
                print(f"⚠️  No valid workers in routing decision, defaulting to MacroDataWorker")
                return {
                    "workers": ["MacroDataWorker"],
                    "reasoning": "Default fallback - no valid workers selected by LLM"
                }
            
            routing_decision["workers"] = valid_workers
            
            print(f"   Selected workers: {', '.join(routing_decision['workers'])}")
            print(f"   Reasoning: {routing_decision.get('reasoning', 'N/A')[:150]}...")
            
            return routing_decision
        
        except Exception as e:
            print(f"⚠️  Routing failed: {str(e)}")
            print(f"   Falling back to MacroDataWorker")
            return {
                "workers": ["MacroDataWorker"],
                "reasoning": f"Fallback due to routing error: {str(e)}"
            }
    
    def _execute_worker(self, worker_name: str, query: str) -> Dict[str, Any]:
        """
        Ejecuta un worker individual.
        
        Args:
            worker_name: Nombre del worker
            query: User query
        
        Returns:
            Dict con resultado del worker
        """
        print(f"\n   🔧 Executing {worker_name}...")
        
        try:
            worker = self._get_worker(worker_name)
            
            # Ejecutar worker
            start_time = datetime.now()
            
            # Different workers have different method signatures
            if worker_name == "MacroDataWorker":
                result = {"success": True, "analysis": worker.analyze_economy(query)}
            elif worker_name == "RegionalContextWorker":
                result = worker.analyze_region(query)
            elif worker_name == "IndicatorAnalysisWorker":
                result = worker.analyze_stock(query)
            else:
                result = {"error": f"Unknown worker method for {worker_name}"}
            
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"      ✅ {worker_name} completed in {duration:.2f}s")
            
            return {
                "worker": worker_name,
                "success": result.get("success", False),
                "result": result,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"      ❌ {worker_name} failed: {str(e)}")
            return {
                "worker": worker_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_workers_parallel(self, workers: List[str], query: str) -> List[Dict[str, Any]]:
        """
        Ejecuta múltiples workers en paralelo.
        
        Args:
            workers: Lista de nombres de workers
            query: User query
        
        Returns:
            Lista de resultados de workers
        """
        print(f"\n⚡ Executing {len(workers)} worker(s) in parallel...")
        
        if len(workers) == 1:
            # No need for parallelization
            return [self._execute_worker(workers[0], query)]
        
        results = []
        with ThreadPoolExecutor(max_workers=len(workers)) as executor:
            future_to_worker = {
                executor.submit(self._execute_worker, worker, query): worker
                for worker in workers
            }
            
            for future in as_completed(future_to_worker):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    worker = future_to_worker[future]
                    print(f"   ❌ Worker {worker} raised exception: {str(e)}")
                    results.append({
                        "worker": worker,
                        "success": False,
                        "error": str(e)
                    })
        
        return results
    
    def _synthesize_results(
        self,
        query: str,
        worker_results: List[Dict[str, Any]]
    ) -> str:
        """
        Sintetiza los resultados de múltiples workers en una respuesta coherente.
        
        Args:
            query: User query original
            worker_results: Lista de resultados de workers
        
        Returns:
            Análisis sintetizado como string
        """
        print(f"\n📝 Synthesizing results from {len(worker_results)} worker(s)...")
        
        # Filter successful results
        successful_results = [r for r in worker_results if r.get("success")]
        
        if not successful_results:
            return "Unable to generate analysis - all workers failed."
        
        # Si solo hay 1 resultado exitoso, retornarlo directamente
        if len(successful_results) == 1:
            result = successful_results[0]
            worker_result = result.get("result", {})
            
            # Extract relevant content
            if "analysis" in worker_result:
                return worker_result["analysis"]
            elif "comparison" in worker_result:
                return worker_result["comparison"]
            else:
                return json.dumps(worker_result, indent=2)
        
        # Multiple workers - need synthesis
        synthesis_prompt = f"""
You are a financial analyst synthesizing information from multiple data sources.

Original query: "{query}"

Data from {len(successful_results)} workers:
"""
        
        for i, result in enumerate(successful_results, 1):
            worker_name = result.get("worker", f"Worker {i}")
            worker_result = result.get("result", {})
            
            # Extract relevant content
            content = ""
            if "analysis" in worker_result:
                content = worker_result["analysis"]
            elif "comparison" in worker_result:
                content = worker_result["comparison"]
            else:
                content = json.dumps(worker_result, indent=2)
            
            synthesis_prompt += f"\n\n{i}. {worker_name} Results:\n{content[:1000]}"
        
        synthesis_prompt += """

Your task:
1. Synthesize the information from all sources into a coherent, comprehensive analysis
2. Address the original query directly
3. Highlight key insights and connections between the data
4. Keep the response clear, concise, and well-structured
5. If there are contradictions, acknowledge them

Provide a comprehensive analysis:
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=synthesis_prompt)])
            synthesized = response.content.strip()
            print(f"   ✅ Synthesis completed ({len(synthesized)} chars)")
            return synthesized
        
        except Exception as e:
            print(f"   ⚠️  Synthesis failed: {str(e)}")
            # Fallback: concatenate results
            fallback = f"Analysis for: {query}\n\n"
            for result in successful_results:
                worker_name = result.get("worker")
                worker_result = result.get("result", {})
                content = worker_result.get("analysis") or worker_result.get("comparison") or str(worker_result)
                fallback += f"\n### {worker_name}:\n{content}\n"
            return fallback
    
    def process(self, query: str) -> Dict[str, Any]:
        """
        Procesa una query macroeconómica usando routing inteligente y múltiples workers.
        
        Args:
            query: User query
        
        Returns:
            Dict con:
            - success: bool
            - query: str - Query original
            - routing: Dict - Decisión de routing
            - workers_executed: int
            - workers_successful: int
            - worker_results: List[Dict] - Resultados de workers
            - analysis: str - Análisis sintetizado
            - duration_seconds: float
            - timestamp: str
        """
        print(f"\n" + "="*70)
        print(f"🎯 MACRO SUPERVISOR - Processing Query")
        print(f"="*70)
        print(f"\nQuery: {query}\n")
        
        start_time = datetime.now()
        
        try:
            # 1. Route query to appropriate workers
            routing_decision = self._route_query(query)
            selected_workers = routing_decision["workers"]
            
            # 2. Execute selected workers
            worker_results = self._execute_workers_parallel(selected_workers, query)
            
            # 3. Synthesize results
            analysis = self._synthesize_results(query, worker_results)
            
            # 4. Compile final result
            duration = (datetime.now() - start_time).total_seconds()
            
            successful_count = sum(1 for r in worker_results if r.get("success"))
            overall_success = successful_count > 0
            
            result = {
                "success": overall_success,
                "query": query,
                "routing": routing_decision,
                "workers_executed": len(worker_results),
                "workers_successful": successful_count,
                "worker_results": worker_results,
                "analysis": analysis,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "supervisor": "MacroSupervisor"
            }
            
            print(f"\n" + "="*70)
            print(f"✅ Processing completed in {duration:.2f}s")
            print(f"   Workers executed: {len(worker_results)}")
            print(f"   Workers successful: {successful_count}")
            print(f"="*70)
            
            return result
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\n❌ Processing failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "supervisor": "MacroSupervisor"
            }


# Example usage
if __name__ == "__main__":
    supervisor = MacroSupervisor()
    
    # Example 1: Simple query (1 worker)
    result1 = supervisor.process("What is the GDP of USA?")
    
    # Example 2: Regional query (1 worker)
    result2 = supervisor.process("What is the economic situation in Argentina?")
    
    # Example 3: Stock query (1 worker)
    result3 = supervisor.process("Analyze Apple stock with RSI indicator")
    
    # Example 4: Complex query (multiple workers)
    result4 = supervisor.process("Compare USA and Argentina economies and analyze GGAL stock")
