# app/agents/research_agent.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from app.market_data import get_market_snapshot
from app.signal_state import SignalState

load_dotenv()

# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3
)

def research_agent(state: SignalState) -> SignalState:
    """
    Agent 1 — Market Research
    - Fetches live market data
    - Analyzes price action and volume
    - Writes a research summary for Agent 2
    """
    print("Agent 1: Fetching market data...")

    # Step 1 — get fresh market data
    market_data = get_market_snapshot()

    # Step 2 — build a prompt for Gemini
    prompt = f"""
You are a professional crypto market analyst.
Analyze the following market data for BTC, ETH, and SOL
and write a short research summary (max 5 lines).

Focus on:
- Price trend direction
- Volume activity (is volume high or low vs average?)
- Any notable price moves in the last hour
- Overall market sentiment (bullish / bearish / neutral)

Market Data:
"""
    for coin, data in market_data.items():
        prompt += f"""
{coin}:
  Price: ${data['price']:,.2f}
  1h Change: {data['price_change_pct']}%
  Volume Ratio: {data['volume_ratio']}x average
  High: ${data['high']:,.2f}
  Low:  ${data['low']:,.2f}
"""

    prompt += "\nWrite a clear, concise research summary:"

    # Step 3 — ask Gemini to summarize
    print("Agent 1: Asking Gemini to analyze...")
    response = llm.invoke(prompt)
    research_summary = response.content

    print(f"Agent 1: Done.\n")
    print(f"--- Research Summary ---")
    print(research_summary)
    print(f"------------------------\n")

    # Step 4 — update state
    return {
        **state,
        "market_data": market_data,
        "research_summary": research_summary
    }


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start with empty state
    initial_state: SignalState = {
        "market_data": {},
        "research_summary": "",
        "candidate_signal": {},
        "human_approved": None,
        "human_feedback": None,
        "final_whatsapp_message": "",
        "compliance_passed": False,
        "delivery_status": "pending",
        "performance_log": {}
    }

    result = research_agent(initial_state)
    print("State after Agent 1:")
    print(f"  research_summary: {result['research_summary'][:100]}...")