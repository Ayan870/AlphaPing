# app/signal_state.py
from typing import TypedDict, Optional

class SignalState(TypedDict):
    # Raw market data from Binance/CoinGecko
    market_data: dict

    # Agent 1 output — market summary + sentiment
    research_summary: str

    # Agent 2 output — the actual trade signal
    candidate_signal: dict
    # Format: {
    #   "pair": "BTCUSDT",
    #   "direction": "LONG" or "SHORT" or "NO_TRADE",
    #   "entry_low": 0.0,
    #   "entry_high": 0.0,
    #   "stop_loss": 0.0,
    #   "tp1": 0.0,
    #   "tp2": 0.0,
    #   "tp3": 0.0,
    #   "confidence": 0,       # 0-100
    #   "risk_score": 0,       # 1-5
    #   "setup_type": "",      # "breakout", "volume_surge", etc.
    #   "timeframe": "1h",
    #   "raw_rationale": ""
    # }

    # Human approval gate
    human_approved: Optional[bool]   # None=pending, True=approved, False=rejected
    human_feedback: Optional[str]    # Admin notes or edit reason

    # Agent 3 output — formatted WhatsApp message
    final_whatsapp_message: str

    # Agent 4 output — compliance check result
    compliance_passed: bool

    # Delivery status
    delivery_status: str  # "pending", "sent", "failed"

    # Performance tracking
    performance_log: dict
    # Format: {
    #   "sent_at": "",
    #   "entry_hit": False,
    #   "tp1_hit": False,
    #   "tp2_hit": False,
    #   "tp3_hit": False,
    #   "sl_hit": False,
    #   "final_pnl": 0.0,
    #   "result": ""    # "win", "loss", "partial", "pending"
    # }