from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..controller.upload_controller import router as upload_router
from ..controller.evaluate_controller import router as evaluate_router
from ..controller.search_controller import router as search_router

# 🔹 Opik configuration
from src.service.opik_config import configure_opik

# ----------------------------------------------------
# Configure Opik when FastAPI starts
# ----------------------------------------------------
configure_opik()

# ----------------------------------------------------
# Initialize FastAPI app
# ----------------------------------------------------
app = FastAPI()

# ----------------------------------------------------
# CORS Configuration
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Include all routers
# ----------------------------------------------------
app.include_router(upload_router, prefix="/api/upload")
app.include_router(evaluate_router, prefix="/api/evaluate")
app.include_router(search_router, prefix="/api/search")
