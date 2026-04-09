# app/agents/compliance_agent.py
from app.signal_state import SignalState

# Words that are banned — regulatory red flags
BANNED_WORDS = [
    "guaranteed", "guarantee",
    "100%", "risk-free", "riskfree",
    "sure profit", "sure win",
    "no loss", "never lose",
    "definitely", "certain profit",
    "get rich", "easy money",
    "double your money",
    "investment advice",
    "financial advice"
]

# Disclaimer that must appear on every signal
REQUIRED_DISCLAIMER = (
    "\n\n⚠️ _Disclaimer: This is not financial advice. "
    "Crypto trading carries significant risk. "
    "Only trade what you can afford to lose. "
    "AlphaPing signals are for informational purposes only._"
)

def compliance_agent(state: SignalState) -> SignalState:
    """
    Agent 4 — Compliance Guardrail
    - Scans message for banned words
    - Forces disclaimer to be present
    - Blocks non-compliant messages
    """
    print("Agent 4: Running compliance check...")

    message = state["final_whatsapp_message"]
    message_lower = message.lower()

    # Check for banned words
    found_banned = []
    for word in BANNED_WORDS:
        if word.lower() in message_lower:
            found_banned.append(word)

    if found_banned:
        print(f"  ❌ Banned words found: {found_banned}")
        print("  Message blocked — returning to messaging agent\n")
        return {
            **state,
            "compliance_passed": False,
            "final_whatsapp_message": ""  # clear message so it gets rewritten
        }

    # Add disclaimer if not already present
    if "disclaimer" not in message_lower and "not financial advice" not in message_lower:
        message = message + REQUIRED_DISCLAIMER
        print("  ✅ Disclaimer added")

    print("  ✅ Compliance check passed\n")

    return {
        **state,
        "final_whatsapp_message": message,
        "compliance_passed": True
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test 1 — clean message (should pass)
    clean_state: SignalState = {
        "market_data": {},
        "research_summary": "",
        "candidate_signal": {},
        "human_approved": True,
        "human_feedback": None,
        "final_whatsapp_message": "🟢 *BTC LONG Signal*\nEntry: $66,000\nSL: $65,000\nTP1: $67,500",
        "compliance_passed": False,
        "delivery_status": "pending",
        "performance_log": {}
    }

    result = compliance_agent(clean_state)
    print(f"Passed: {result['compliance_passed']}")
    print(f"Message:\n{result['final_whatsapp_message']}\n")

    # Test 2 — banned word (should fail)
    dirty_state = {
        **clean_state,
        "final_whatsapp_message": "🟢 *BTC LONG* — guaranteed profit! Entry: $66,000"
    }

    result2 = compliance_agent(dirty_state)
    print(f"Passed: {result2['compliance_passed']}")