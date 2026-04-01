# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # ── App ──────────────────────────────────
    APP_NAME:    str = "AlphaPing"
    APP_VERSION: str = "1.0.0"
    DEBUG:       bool = True

    # ── AI / LLM ─────────────────────────────
    GEMINI_API_KEY:  str = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL:    str = os.getenv("OLLAMA_MODEL", "qwen2.5")
    
    # Active model — change this to switch between models
    # Options: "gemini" or "ollama"
    ACTIVE_MODEL:    str = os.getenv("ACTIVE_MODEL", "ollama")

    # ── Market Data ──────────────────────────
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET:  str = os.getenv("BINANCE_SECRET", "")
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")

    # ── WhatsApp ─────────────────────────────
    WHATSAPP_PHONE_NUMBER_ID:    str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ACCESS_TOKEN:       str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")

    # ── Database ─────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_PATH:      str = "alphaping.db"

    # ── Redis ────────────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # ── Stripe ───────────────────────────────
    STRIPE_SECRET_KEY:      str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

    # ── Trading ──────────────────────────────
    PAIRS: dict = {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "SOL": "SOLUSDT"
    }
    MIN_CONFIDENCE:    int = 60
    MAX_SIGNALS_PER_DAY: int = 3
    SIGNAL_INTERVAL_MIN: int = 15


# Single instance used everywhere
settings = Settings()


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"App:     {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Gemini:  {'✅ set' if settings.GEMINI_API_KEY else '❌ missing'}")
    print(f"Binance: {'✅ set' if settings.BINANCE_API_KEY else '❌ missing'}")
    print(f"CoinGecko: {'✅ set' if settings.COINGECKO_API_KEY else '❌ missing'}")
    print(f"WhatsApp: {'✅ set' if settings.WHATSAPP_ACCESS_TOKEN else '❌ not set yet'}")
    print(f"Min confidence: {settings.MIN_CONFIDENCE}")
    print(f"Pairs: {list(settings.PAIRS.keys())}")