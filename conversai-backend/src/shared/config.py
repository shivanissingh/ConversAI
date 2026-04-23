"""
Shared Configuration Module

Provides centralized configuration for all components.
Environment variables are loaded from .env file in main.py at startup.
"""

import os
from pydantic import BaseModel, Field
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    OLLAMA = "ollama"


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    # Application info
    app_name: str = "ConversAI Backend"
    version: str = "1.0.0"
    
    # ==========================================================================
    # LLM Provider Configuration
    # Set LLM_PROVIDER to "gemini" (default) or "ollama" to switch providers
    # ==========================================================================
    llm_provider: str = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini")
    )
    
    # ==========================================================================
    # Google Gemini Configuration (Default Provider)
    # GEMINI_API_KEY must be set in .env file for Gemini to work
    # Default model: gemini-3-flash-preview
    # ==========================================================================
    gemini_api_key: str = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )
    gemini_model: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    )
    
    # ==========================================================================
    # Ollama Configuration (Optional Fallback)
    # Used when LLM_PROVIDER=ollama
    # ==========================================================================
    ollama_base_url: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    ollama_model: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2")
    )
    
    # Explanation Engine Configuration
    speaking_rate_wpm: int = 150  # Words per minute for timing calculation
    
    # ==========================================================================
    # Visual Engine Configuration (Hugging Face Inference API)
    # IMAGE_PROVIDER should be "hf_inference" for V1
    # HF_API_KEY must be set in .env file
    # ==========================================================================
    image_provider: str = Field(
        default_factory=lambda: os.getenv("IMAGE_PROVIDER", "hf_inference")
    )
    hf_api_key: str = Field(
        default_factory=lambda: os.getenv("HF_API_KEY", "")
    )
    image_model: str = Field(
        default_factory=lambda: os.getenv("IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
    )
    image_width: int = Field(
        default_factory=lambda: int(os.getenv("IMAGE_WIDTH", "1024"))
    )
    image_height: int = Field(
        default_factory=lambda: int(os.getenv("IMAGE_HEIGHT", "1024"))
    )
    
    # Timeouts (seconds)
    llm_timeout: float = 120.0
    image_timeout: float = 60.0
    
    def validate_gemini_api_key(self) -> None:
        """
        Validate that GEMINI_API_KEY is set when using Gemini provider.
        Called at application startup in main.py.
        Raises ValueError if missing or placeholder.
        """
        if self.llm_provider == LLMProvider.GEMINI.value:
            if not self.gemini_api_key:
                raise ValueError(
                    "GEMINI_API_KEY environment variable is required when using Gemini provider.\n"
                    "Set it in .env file: GEMINI_API_KEY=your-actual-api-key\n"
                    "Or switch to Ollama: LLM_PROVIDER=ollama"
                )
            if self.gemini_api_key == "YOUR_GEMINI_API_KEY_HERE":
                raise ValueError(
                    "GEMINI_API_KEY contains placeholder value.\n"
                    "Please replace with your actual API key in .env file.\n"
                    "Get your key from: https://aistudio.google.com/apikey"
                )
    
    def validate_hf_api_key(self) -> None:
        """
        Validate that HF_API_KEY is set when using Visual Engine.
        Called when Visual Engine is invoked.
        Raises ValueError if missing or placeholder.
        """
        if self.image_provider == "hf_inference":
            if not self.hf_api_key:
                raise ValueError(
                    "HF_API_KEY environment variable is required for Visual Engine.\n"
                    "Set it in .env file: HF_API_KEY=your-actual-api-key\n"
                    "Get your key from: https://huggingface.co/settings/tokens"
                )
            if self.hf_api_key in ["YOUR_HF_API_KEY", "hf_..."]:
                raise ValueError(
                    "HF_API_KEY contains placeholder value.\n"
                    "Please replace with your actual API key in .env file.\n"
                    "Get your key from: https://huggingface.co/settings/tokens"
                )


# Singleton settings instance
settings = Settings()
