
# test_graph.py
from app.signal_state import SignalState
from app.graph import build_graph

# Force a high confidence signal for testing
state: SignalState = {
    "market_data": {},
    "research_summary": "BTC strong breakout above resistance with high volume.",
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
        "raw_rationale": "BTC broke above 20-period high with volume confirmation."
    },
    "human_approved": None,
    "human_feedback": None,
    "final_whatsapp_message": "",
    "compliance_passed": False,
    "delivery_status": "pending",
    "performance_log": {}
}

app = build_graph()
config = {"configurable": {"thread_id": "test-signal-001"}}
result = app.invoke(state, config=config)

print("Final status:", result["delivery_status"])