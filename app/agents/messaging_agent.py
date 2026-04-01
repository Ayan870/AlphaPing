# app/agents/messaging_agent.py
import os
from app.signal_state import SignalState
from app.core.llm import get_llm

def messaging_agent(state: SignalState) -> SignalState:
    """
    Agent 3 — Messaging
    Converts candidate signal into clean WhatsApp message
    """
    print("Agent 3: Formatting WhatsApp message...")

    signal = state["candidate_signal"]

    # If no trade, send a simple update
    if signal.get("direction") == "NO_TRADE":
        message = (
            "📊 *AlphaPing Market Update*\n\n"
            "No high-confidence setup detected right now.\n"
            "We only send signals when conditions are right.\n\n"
            "🔍 Monitoring BTC | ETH | SOL\n"
            "⏳ Next scan in 15 minutes\n\n"
            "_Risk disclaimer: This is not financial advice._"
        )
        return {
            **state,
            "final_whatsapp_message": message
        }

    # Build prompt for real signal
    direction_emoji = "🟢 LONG" if signal["direction"] == "LONG" else "🔴 SHORT"
    risk_stars = "⭐" * (6 - signal["risk_score"])

    prompt = f"""
You are a professional crypto signal writer for WhatsApp.
Write a clean, clear trading signal message based on this data.

Rules:
- Use simple language (beginner friendly)
- Keep it under 200 words
- Use emojis sparingly
- Never say "guaranteed", "risk-free", "100% profit"
- Always include the disclaimer at the end
- Format it for WhatsApp (use *bold* with asterisks)

Signal Data:
- Pair: {signal['pair']}
- Direction: {signal['direction']}
- Entry Zone: ${signal['entry_low']:,.2f} - ${signal['entry_high']:,.2f}
- Stop Loss: ${signal['stop_loss']:,.2f}
- Take Profit 1: ${signal['tp1']:,.2f}
- Take Profit 2: ${signal['tp2']:,.2f}
- Take Profit 3: ${signal['tp3']:,.2f}
- Setup Type: {signal['setup_type']}
- Confidence: {signal['confidence']}/100
- Risk Score: {signal['risk_score']}/5
- Timeframe: {signal['timeframe']}
- Analysis: {signal['raw_rationale']}

Write the WhatsApp signal message now:
"""

    llm      = get_llm(temperature=0.4)
    response = llm.invoke(prompt)
    message = response.content if hasattr(response, 'content') else response

    print("Agent 3: Message formatted.\n")
    print("--- WhatsApp Message Preview ---")
    print(message)
    print("--------------------------------\n")

    return {
        **state,
        "final_whatsapp_message": message
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Simulate a signal for testing
    test_state: SignalState = {
        "market_data": {},
        "research_summary": "BTC showing strong breakout above resistance with 2x volume surge. Bullish momentum building.",
        "candidate_signal": {
            "pair": "BTCUSDT",
            "coin": "BTC",
            "direction": "LONG",
            "entry_low": 66000.0,
            "entry_high": 66300.0,
            "stop_loss": 65000.0,
            "tp1": 67500.0,
            "tp2": 68500.0,
            "tp3": 70000.0,
            "confidence": 78,
            "risk_score": 2,
            "setup_type": "breakout",
            "timeframe": "1h",
            "raw_rationale": "BTC broke above 20-period high with strong volume confirmation."
        },
        "human_approved": True,
        "human_feedback": None,
        "final_whatsapp_message": "",
        "compliance_passed": False,
        "delivery_status": "pending",
        "performance_log": {}
    }

    result = messaging_agent(test_state)