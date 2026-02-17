import opik
from opik import track, opik_context
from functools import wraps
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