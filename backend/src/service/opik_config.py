"""Opik configuration for 0xnavi services."""
import opik
import os


def configure_opik():
    """Configure Opik - uses existing config or environment variables."""
    try:
        url_override = os.getenv("OPIK_URL_OVERRIDE")
        
        if url_override:
            opik.configure(url=url_override)
            
        print(f"OPIK: Configuration completed successfully.")
    except Exception as e:
        print(f"OPIK: Using existing configuration.")


def get_opik_client():
    """Get configured Opik client."""
    configure_opik()
    return opik
