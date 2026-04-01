# app/core/llm.py
from app.core.config import settings


def get_llm(temperature: float = 0.3):
    """
    Returns the active LLM based on settings.ACTIVE_MODEL.
    Change ACTIVE_MODEL in .env to switch between models:
        ACTIVE_MODEL=gemini  → uses Gemini API
        ACTIVE_MODEL=ollama  → uses local Ollama (free, unlimited)
    """
    if settings.ACTIVE_MODEL == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        print(f"🤖 Using Gemini: gemini-2.5-flash-lite")
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature
        )

    else:  # ollama (default)
        from langchain_community.llms import Ollama
        print(f"🤖 Using Ollama: {settings.OLLAMA_MODEL}")
        return Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=temperature
        )


def get_active_model_name() -> str:
    """Returns the name of the currently active model"""
    if settings.ACTIVE_MODEL == "gemini":
        return "Gemini 2.5 Flash Lite"
    return f"Ollama ({settings.OLLAMA_MODEL})"