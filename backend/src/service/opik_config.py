"""Opik configuration for 0xnavi services."""
import opik

def configure_opik():
    """Configure Opik to use local instance."""
    try:
        opik.configure(opik_url="http://localhost:5173/api")
    except Exception:
        pass

def get_opik_client():
    """Get configured Opik client."""
    configure_opik()
    return opik