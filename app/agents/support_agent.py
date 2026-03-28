# app/agents/support_agent.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from app.signal_state import SignalState

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.5
)

# ── Known commands ────────────────────────────────────────────────────────────
COMMANDS = {
    "JOIN":    "User wants to subscribe to signals",
    "STOP":    "User wants to unsubscribe",
    "DETAILS": "User wants details about the last signal",
    "PLAN":    "User wants to know about pricing plans",
    "HELP":    "User needs general help",
}

# ── Plan info ─────────────────────────────────────────────────────────────────
PLAN_INFO = """
*AlphaPing Signal Plans:*

🆓 *Free* — $0/month
- Delayed signals (15-30 min lag)
- BTC only
- 1 signal per day

⭐ *Pro* — $29/month  
- Real-time signals
- BTC + ETH + SOL
- Full TP/SL updates
- Daily market recap

💎 *VIP* — $149/month
- Everything in Pro
- 6-8 trading pairs
- Daily market commentary
- Priority WhatsApp support
- Monthly portfolio review

Reply *JOIN PRO* or *JOIN VIP* to upgrade.
"""

def handle_command(command: str) -> str:
    """Handle known WhatsApp commands"""
    command = command.strip().upper()

    if command == "JOIN":
        return (
            "👋 *Welcome to AlphaPing!*\n\n"
            "You are now on the *Free* plan.\n"
            "You will receive 1 delayed signal per day for BTC.\n\n"
            "To upgrade to real-time signals reply *PLAN*\n\n"
            "⚠️ _Disclaimer: Signals are not financial advice. "
            "Trade responsibly._"
        )

    elif command == "STOP":
        return (
            "✅ You have been unsubscribed from AlphaPing signals.\n\n"
            "We are sorry to see you go.\n"
            "Reply *JOIN* anytime to resubscribe.\n\n"
            "_Your data has been removed._"
        )

    elif command == "PLAN":
        return PLAN_INFO

    elif command == "HELP":
        return (
            "🤖 *AlphaPing Help*\n\n"
            "Available commands:\n"
            "• *JOIN* — Subscribe to signals\n"
            "• *STOP* — Unsubscribe\n"
            "• *DETAILS* — Get last signal details\n"
            "• *PLAN* — View pricing plans\n"
            "• *HELP* — Show this message\n\n"
            "For anything else just type your question."
        )

    return None  # Not a known command — use AI


def support_agent(user_message: str, last_signal: dict = None) -> str:
    """
    Agent 5 — Support
    Handles user WhatsApp replies.
    Known commands get instant responses.
    Unknown questions go to Gemini.
    """
    print(f"Agent 5: Handling message: '{user_message}'")

    # Check known commands first
    command_response = handle_command(user_message)
    if command_response:
        print("Agent 5: Matched known command.\n")
        return command_response

    # Handle DETAILS separately (needs last signal)
    if user_message.strip().upper() == "DETAILS":
        if last_signal and last_signal.get("direction") != "NO_TRADE":
            return (
                f"📊 *Last Signal Details*\n\n"
                f"Pair: {last_signal.get('pair', 'N/A')}\n"
                f"Direction: {last_signal.get('direction', 'N/A')}\n"
                f"Entry: ${last_signal.get('entry_low', 0):,.2f} - "
                f"${last_signal.get('entry_high', 0):,.2f}\n"
                f"Stop Loss: ${last_signal.get('stop_loss', 0):,.2f}\n"
                f"TP1: ${last_signal.get('tp1', 0):,.2f}\n"
                f"TP2: ${last_signal.get('tp2', 0):,.2f}\n"
                f"TP3: ${last_signal.get('tp3', 0):,.2f}\n"
                f"Confidence: {last_signal.get('confidence', 0)}/100\n\n"
                f"⚠️ _Not financial advice. Trade responsibly._"
            )
        return "No active signal right now. We will notify you when the next setup is detected."

    # Unknown message — use Gemini to respond
    print("Agent 5: Unknown message — asking Gemini...")
    prompt = f"""
You are a helpful support agent for AlphaPing, a crypto signal service.
Answer the user's question clearly and briefly (max 5 lines).

Rules:
- Never promise profits or guaranteed returns
- Always mention risk when discussing trading
- If asked about signals, explain we use AI + human approval
- Be friendly and professional
- End with the disclaimer if discussing trades

User message: {user_message}

Reply:
"""
    response = llm.invoke(prompt)
    reply = response.content + (
        "\n\n⚠️ _Disclaimer: Not financial advice. "
        "Trade responsibly._"
    )
    print("Agent 5: Done.\n")
    return reply


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_messages = ["JOIN", "PLAN", "STOP", "HELP", "What is your win rate?"]
    
    for msg in test_messages:
        print(f"\n{'='*40}")
        print(f"User: {msg}")
        print(f"{'='*40}")
        reply = support_agent(msg)
        print(f"Bot: {reply}")