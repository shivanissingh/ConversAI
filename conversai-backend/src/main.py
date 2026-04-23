"""
ConversAI Backend - Application Entry Point

Loads environment variables from .env and initializes the FastAPI application.
"""

# =============================================================================
# Load environment variables FIRST, before any other imports
# This ensures all modules read the correct config values
# =============================================================================
from dotenv import load_dotenv
load_dotenv()  # Loads .env file from backend root

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.shared.config import settings
from src.api.routes import health, explanation
from src.api.middleware.error_handler import global_exception_handler

# Validate critical configuration at startup
settings.validate_gemini_api_key()

app = FastAPI(title=settings.app_name, version=settings.version)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)

# Routes
app.include_router(health.router, prefix="/api")
app.include_router(explanation.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
