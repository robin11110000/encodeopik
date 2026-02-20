import opik
from opik import track, opik_context
from functools import wraps
import time
import psutil
import os
import logging

logger = logging.getLogger(__name__)


def _safe_set_metadata(span, metadata):
    """Safely set metadata on a span, ignoring errors."""
    try:
        if span is not None and hasattr(span, 'set_metadata') and callable(span.set_metadata):
            span.set_metadata(metadata)
    except Exception as e:
        logger.warning(f"Failed to set metadata on span: {e}")


def _safe_get_current_span():
    """Safely get current span, returning None on failure."""
    try:
        return opik.get_current_span()
    except Exception as e:
        logger.warning(f"Failed to get current span: {e}")
        return None


def trace_service_call(service_name):
    """Decorator to trace service method calls."""
    def decorator(func):
        @track(name=f"{service_name}.{func.__name__}")
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def trace_with_metadata(name, capture_input=True, capture_output=True):
    """Advanced tracer with metadata capture."""
    def decorator(func):
        @track(name=name, capture_input=capture_input, capture_output=capture_output)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def track_with_error_context(operation_name: str):
    """Decorator for tracking with detailed error context.
    
    Tracks success/failure status, error types, and operation details.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Log success metrics
                current_span = _safe_get_current_span()
                _safe_set_metadata(current_span, {
                    "status": "success",
                    "operation": operation_name,
                })
                
                return result
                
            except Exception as e:
                # Enhanced error logging
                current_span = _safe_get_current_span()
                _safe_set_metadata(current_span, {
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "operation": operation_name,
                })
                raise
        return wrapper
    return decorator


# =============================================================================
# PERFORMANCE MONITORING DECORATOR
# =============================================================================

def track_performance(func):
    """Decorator for tracking performance metrics.
    
    Tracks execution time, performance tier, memory usage, and alerts on slow operations.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        span = None
        try:
            span = opik.get_current_span()
        except Exception:
            pass
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Get memory usage
            try:
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
            except Exception:
                memory_mb = None
            
            # Set performance metadata
            perf_data = {
                "execution_time_ms": round(execution_time * 1000, 2),
                "performance_tier": get_performance_tier(execution_time),
                "memory_usage_mb": round(memory_mb, 2) if memory_mb else None,
                "status": "completed"
            }
            _safe_set_metadata(span, perf_data)
            
            # Alert on slow operations (>10 seconds)
            if execution_time > 10:
                _safe_set_metadata(span, {
                    "alert": "slow_operation",
                    "threshold_exceeded": True
                })
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            _safe_set_metadata(span, {
                "error": str(e),
                "execution_time_ms": round(execution_time * 1000, 2)
            })
            raise
    return wrapper


def get_performance_tier(execution_time: float) -> str:
    """Categorize execution time into performance tiers."""
    if execution_time < 1:
        return "fast"
    elif execution_time < 5:
        return "normal"
    elif execution_time < 10:
        return "slow"
    else:
        return "very_slow"


# =============================================================================
# BUSINESS METRICS TRACKING
# =============================================================================

def track_business_metrics(operation_name: str):
    """Decorator for tracking business-relevant metrics.
    
    Tracks document type, processing success, fraud detection, confidence scores.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            span = None
            try:
                span = opik.get_current_span()
            except Exception:
                pass
            
            try:
                result = func(*args, **kwargs)
                
                # Extract metrics from result if available
                metrics = {
                    "operation": operation_name,
                    "processing_success": True,
                }
                
                # Add specific metrics based on operation type
                if "fraud" in operation_name.lower():
                    if isinstance(result, dict):
                        metrics["fraud_detected"] = result.get("fraud_detected", False)
                        metrics["confidence_score"] = result.get("confidence", 0)
                
                _safe_set_metadata(span, metrics)
                
                return result
                
            except Exception as e:
                _safe_set_metadata(span, {
                    "processing_success": False,
                    "error": str(e),
                    "operation": operation_name
                })
                raise
        return wrapper
    return decorator


# =============================================================================
# RAG QUERY ENHANCEMENT
# =============================================================================

def track_rag_query(func):
    """Decorator for enhanced RAG query tracking.
    
    Tracks retrieval count, scores, query type, response length, and context usage.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        query = kwargs.get('query') or (args[0] if args else '')
        
        span = None
        try:
            span = opik.get_current_span()
        except Exception:
            pass
        
        try:
            result = func(*args, **kwargs)
            
            # Determine query type
            query_type = classify_query_type(query)
            
            # Extract retrieval info if available
            retrieval_count = 0
            retrieval_scores = []
            
            if isinstance(result, dict):
                retrieval_count = len(result.get("matches", []))
                retrieval_scores = [m.get("score", 0) for m in result.get("matches", [])]
            
            rag_data = {
                "query_type": query_type,
                "retrieval_count": retrieval_count,
                "avg_retrieval_score": sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0,
                "response_length": len(result.get("answer", "")) if isinstance(result, dict) else 0,
            }
            _safe_set_metadata(span, rag_data)
            
            return result
            
        except Exception as e:
            _safe_set_metadata(span, {
                "error": str(e),
                "query_type": classify_query_type(query)
            })
            raise
    return wrapper


def classify_query_type(query: str) -> str:
    """Classify query type based on content."""
    if not query:
        return "unknown"
    
    query_lower = query.lower()
    
    if "?" in query:
        return "question"
    elif any(word in query_lower for word in ["find", "search", "show", "get", "list"]):
        return "search"
    elif any(word in query_lower for word in ["compare", "vs", "difference", "versus"]):
        return "comparison"
    elif any(word in query_lower for word in ["how many", "count", "total", "sum"]):
        return "aggregation"
    elif any(word in query_lower for word in ["what is", "tell me", "explain"]):
        return "informational"
    else:
        return "general"
