# app/services/signal_service.py
import uuid
import asyncio
from app.core.config import settings
from app.core.database import save_signal
from app.graph import build_graph
from app.signal_state import SignalState
from app.services.websocket_service import (
    set_candle_close_callback,
    get_latest_candles,
    latest_candles
)

# Track how many signals sent today (max 3)
signals_sent_today = 0
last_signal_date   = None

# Import shared pending_signals from API router
from app.core.database import save_pending_signal


def reset_daily_counter():
    """Reset signal counter at start of new day"""
    global signals_sent_today, last_signal_date
    from datetime import date
    today = date.today().isoformat()
    if last_signal_date != today:
        signals_sent_today = 0
        last_signal_date   = today


def can_send_signal() -> bool:
    """Check if we can send more signals today"""
    reset_daily_counter()
    return signals_sent_today < settings.MAX_SIGNALS_PER_DAY


async def run_pipeline(thread_id: str, market_data: dict = None):
    """
    Runs the full LangGraph pipeline.
    Called by WebSocket when candle closes OR manually via API.
    """
    global signals_sent_today

    print(f"\n🚀 Pipeline starting — thread_id: {thread_id}")

    try:
        graph = build_graph()

        initial_state: SignalState = {
            "market_data":             market_data or {},
            "research_summary":        "",
            "candidate_signal":        {},
            "human_approved":          None,
            "human_feedback":          None,
            "final_whatsapp_message":  "",
            "compliance_passed":       False,
            "delivery_status":         "pending",
            "performance_log":         {}
        }

        config      = {"configurable": {"thread_id": thread_id}}
        final_state = graph.invoke(initial_state, config=config)

        # Save to database
        save_signal(thread_id, final_state)

        # Track daily signal count
        if final_state.get("delivery_status") == "sent":
            signals_sent_today += 1
            print(f"📊 Signals sent today: {signals_sent_today}/{settings.MAX_SIGNALS_PER_DAY}")

        # Store pending signals for approval
        if final_state.get("delivery_status") == "pending":
            pending_signals[thread_id] = {
                "state":  final_state,
                "config": config,
                "graph":  graph
            }
            print(f"⏳ Signal pending approval — {thread_id}")
        else:
            print(f"✅ Pipeline complete — {final_state['delivery_status']}")

        return final_state

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return None


async def on_candle_close(symbol: str, candle: dict):
    """
    Called automatically by WebSocket every time a candle closes.
    This is the event-driven trigger for signal generation.
    """
    print(f"\n📡 Signal service received candle close: {symbol}")

    # Check daily limit
    if not can_send_signal():
        print(f"⛔ Daily signal limit reached ({settings.MAX_SIGNALS_PER_DAY}). Skipping.")
        return

    # Build market data from WebSocket candles
    market_data = {}
    for coin, pair in settings.PAIRS.items():
        candles = get_latest_candles(pair, limit=50)
        if not candles:
            print(f"⚠️  No candle data for {pair} yet — skipping")
            continue

        latest  = candles[-1]
        prev    = candles[-2] if len(candles) > 1 else latest
        avg_vol = sum(c["volume"] for c in candles[:-1]) / max(len(candles) - 1, 1)

        market_data[coin] = {
            "symbol":           pair,
            "price":            latest["close"],
            "open":             latest["open"],
            "high":             latest["high"],
            "low":              latest["low"],
            "volume":           latest["volume"],
            "volume_ratio":     round(latest["volume"] / avg_vol if avg_vol > 0 else 1.0, 2),
            "price_change_pct": round(
                ((latest["close"] - prev["close"]) / prev["close"]) * 100, 2
            ),
            "candles":          candles
        }

    if not market_data:
        print("⚠️  No market data available yet — waiting for more candles")
        return

    # Generate unique thread ID and run pipeline
    thread_id = str(uuid.uuid4())
    print(f"🎯 Triggering pipeline for {symbol} close — thread_id: {thread_id}")
    await run_pipeline(thread_id, market_data)


def start_signal_service():
    """
    Registers the candle close callback with the WebSocket service.
    Call this once when the server starts.
    """
    set_candle_close_callback(on_candle_close)
    print("✅ Signal service started — waiting for candle closes")


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from app.services.websocket_service import start_websocket_streams

    async def main():
        print("Starting signal service with WebSocket...")
        print("Pipeline will trigger on every 1h candle close")
        print("Press Ctrl+C to stop\n")

        # Register callback
        start_signal_service()

        # Start WebSocket streams
        await start_websocket_streams()

    asyncio.run(main())