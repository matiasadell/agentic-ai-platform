"""Worker response validator con retry + fallback + graceful degradation.

Este módulo implementa validación robusta de respuestas de workers:
1. Valida con Pydantic schemas
2. Retry automático si falla validación (1-2 intentos)
3. Fallback a error response válido si falla todo
4. Graceful degradation: SIEMPRE retorna un objeto válido
5. Structured logging de errores
"""

import time
import logging
from typing import Dict, Any, Type, Optional, Callable
from pydantic import BaseModel, ValidationError
from .base import WorkerResponse

# Setup structured logging
logger = logging.getLogger(__name__)


class WorkerValidator:
    """Validador robusto de worker responses.
    
    Implementa el patrón: execute → validate → retry → fallback → always return valid.
    
    Ejemplo:
        validator = WorkerValidator()
        
        result = validator.execute_with_validation(
            worker=sentiment_worker,
            method="analyze_sentiment",
            params={"query": "market", "days_back": 7},
            response_schema=SentimentResponse,
            max_retries=2
        )
        
        # result es SIEMPRE un objeto SentimentResponse válido
        # Incluso si el worker falló, result.success=False pero el objeto es válido
    """
    
    def __init__(self, enable_logging: bool = True):
        """Inicializar validator.
        
        Args:
            enable_logging: Si True, loggea eventos de validación
        """
        self.enable_logging = enable_logging
        self.failure_counts: Dict[str, int] = {}  # Track failures por worker
        self.circuit_open: Dict[str, bool] = {}   # Circuit breaker state
    
    def execute_with_validation(
        self,
        worker: Any,
        method: str,
        params: Dict[str, Any],
        response_schema: Type[BaseModel],
        max_retries: int = 2
    ) -> BaseModel:
        """Ejecuta worker con validación robusta.
        
        Este es el método principal. Siempre retorna un objeto válido.
        
        Args:
            worker: Instancia del worker
            method: Nombre del método a ejecutar
            params: Parámetros para el método
            response_schema: Schema Pydantic para validar respuesta
            max_retries: Número máximo de intentos
            
        Returns:
            Objeto validado del tipo response_schema
            SIEMPRE retorna un objeto válido (con success=False si falló)
        """
        worker_name = getattr(worker, 'name', worker.__class__.__name__)
        start_time = time.time()
        
        # Check circuit breaker
        if self.circuit_open.get(worker_name, False):
            logger.warning(
                f"Circuit breaker open for {worker_name}",
                extra={"worker": worker_name, "method": method}
            )
            return self._create_error_response(
                worker_name, method, params,
                error="Circuit breaker open - too many failures",
                error_type="CIRCUIT_OPEN",
                response_schema=response_schema
            )
        
        # Retry loop
        for attempt in range(max_retries):
            try:
                # Ejecutar worker
                raw_result = getattr(worker, method)(**params)
                
                # Validar con Pydantic
                validated = response_schema(**raw_result)
                
                # Success! Reset failure count
                self.failure_counts[worker_name] = 0
                
                execution_time = time.time() - start_time
                if self.enable_logging:
                    logger.info(
                        f"Worker {worker_name}.{method} succeeded",
                        extra={
                            "worker": worker_name,
                            "method": method,
                            "execution_time": execution_time,
                            "attempt": attempt + 1,
                            "success": validated.success
                        }
                    )
                
                return validated
                
            except ValidationError as e:
                # Error de validación de Pydantic
                error_details = self._format_validation_error(e)
                
                if attempt < max_retries - 1:
                    # Retry con feedback
                    if self.enable_logging:
                        logger.warning(
                            f"Validation failed for {worker_name}.{method}, retrying",
                            extra={
                                "worker": worker_name,
                                "method": method,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "error": error_details
                            }
                        )
                    continue
                else:
                    # Último intento falló → fallback
                    self._increment_failure_count(worker_name)
                    
                    if self.enable_logging:
                        logger.error(
                            f"Validation failed after {max_retries} attempts",
                            extra={
                                "worker": worker_name,
                                "method": method,
                                "error": error_details,
                                "raw_result_type": type(raw_result).__name__
                            }
                        )
                    
                    return self._create_error_response(
                        worker_name, method, params,
                        error=f"Validation error: {error_details}",
                        error_type="VALIDATION_ERROR",
                        response_schema=response_schema
                    )
                    
            except Exception as e:
                # Error de ejecución (no de validación)
                self._increment_failure_count(worker_name)
                
                if self.enable_logging:
                    logger.error(
                        f"Execution error in {worker_name}.{method}",
                        extra={
                            "worker": worker_name,
                            "method": method,
                            "error": str(e),
                            "error_type": type(e).__name__
                        },
                        exc_info=True
                    )
                
                return self._create_error_response(
                    worker_name, method, params,
                    error=str(e),
                    error_type="EXECUTION_ERROR",
                    response_schema=response_schema
                )
        
        # No debería llegar aquí, pero por si acaso
        return self._create_error_response(
            worker_name, method, params,
            error="Unknown error - max retries exceeded",
            error_type="UNKNOWN_ERROR",
            response_schema=response_schema
        )
    
    def _create_error_response(
        self,
        worker_name: str,
        method: str,
        params: Dict[str, Any],
        error: str,
        error_type: str,
        response_schema: Type[BaseModel]
    ) -> BaseModel:
        """Crea una respuesta de error válida que cumple el schema.
        
        Esto es clave para graceful degradation: incluso si el worker falla,
        el supervisor recibe un objeto válido que puede procesar.
        """
        error_data = {
            "success": False,
            "worker_name": worker_name,
            "query": params.get('query', params.get('symbol', 'unknown')),
            "error": error,
            "error_type": error_type,
            "metadata": {
                "method": method,
                "params": params
            }
        }
        
        # Intentar crear con el schema específico
        try:
            return response_schema(**error_data)
        except ValidationError:
            # Si falla, usar WorkerResponse base (más permisivo)
            return WorkerResponse(**error_data)
    
    def _format_validation_error(self, error: ValidationError) -> str:
        """Formatea un ValidationError de Pydantic en mensaje legible."""
        errors = error.errors()
        if len(errors) == 1:
            e = errors[0]
            return f"{e['loc']}: {e['msg']}"
        else:
            return f"{len(errors)} validation errors: " + "; ".join(
                f"{e['loc']}: {e['msg']}" for e in errors[:3]  # Solo primeros 3
            )
    
    def _increment_failure_count(self, worker_name: str):
        """Incrementa contador de fallos y abre circuit breaker si necesario."""
        self.failure_counts[worker_name] = self.failure_counts.get(worker_name, 0) + 1
        
        # Abrir circuit breaker después de 5 fallos consecutivos
        if self.failure_counts[worker_name] >= 5:
            self.circuit_open[worker_name] = True
            logger.error(
                f"Circuit breaker opened for {worker_name} after 5 failures",
                extra={"worker": worker_name, "failure_count": self.failure_counts[worker_name]}
            )
    
    def reset_circuit_breaker(self, worker_name: str):
        """Reset manual del circuit breaker (para testing o recovery)."""
        self.circuit_open[worker_name] = False
        self.failure_counts[worker_name] = 0
        logger.info(f"Circuit breaker reset for {worker_name}")