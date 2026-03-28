# app/agents/growth_agent.py
import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.6
)

def generate_daily_recap(performance_records: list) -> str:
    """
    Generates a daily performance recap message
    to be sent to all subscribers via WhatsApp broadcast.

    performance_records = list of signals sent today with results
    """
    print("Agent 6: Generating daily recap...")

    if not performance_records:
        return (
            "📊 *AlphaPing Daily Recap*\n\n"
            f"📅 {datetime.now().strftime('%B %d, %Y')}\n\n"
            "No signals were sent today.\n"
            "Market conditions did not meet our quality threshold.\n\n"
            "We only send signals when we have high confidence.\n"
            "Quality over quantity — always.\n\n"
            "⚠️ _Not financial advice. Trade responsibly._"
        )

    # Calculate stats
    total   = len(performance_records)
    wins    = sum(1 for r in performance_records if r.get("result") == "win")
    losses  = sum(1 for r in performance_records if r.get("result") == "loss")
    pending = sum(1 for r in performance_records if r.get("result") == "pending")
    win_rate = round((wins / total) * 100) if total > 0 else 0

    # Build signal summary
    signal_lines = ""
    for r in performance_records:
        emoji = "✅" if r.get("result") == "win" else "❌" if r.get("result") == "loss" else "⏳"
        signal_lines += (
            f"{emoji} {r.get('pair', 'N/A')} {r.get('direction', '')} — "
            f"{r.get('result', 'pending').upper()}\n"
        )

    # Use Gemini to write the commentary
    prompt = f"""
Write a short daily market commentary (3-4 lines) for crypto traders.
Today's performance: {wins} wins, {losses} losses, {pending} pending out of {total} signals.
Win rate: {win_rate}%.
Be honest, professional, and never promise future profits.
"""
    commentary = llm.invoke(prompt).content

    recap = (
        f"📊 *AlphaPing Daily Recap*\n"
        f"📅 {datetime.now().strftime('%B %d, %Y')}\n\n"
        f"*Today's Signals:*\n"
        f"{signal_lines}\n"
        f"*Stats:* {wins}W / {losses}L / {pending} Pending\n"
        f"*Win Rate:* {win_rate}%\n\n"
        f"*Market Commentary:*\n{commentary}\n\n"
        f"⚠️ _Not financial advice. Past performance does not "
        f"guarantee future results._"
    )

    print("Agent 6: Recap generated.\n")
    return recap


def generate_weekly_content(weekly_stats: dict) -> dict:
    """
    Generates weekly Twitter/YouTube content for growth.
    Returns dict with twitter_thread and youtube_script.
    """
    print("Agent 6: Generating weekly content...")

    stats_text = (
        f"Signals sent: {weekly_stats.get('total_signals', 0)}\n"
        f"Win rate: {weekly_stats.get('win_rate', 0)}%\n"
        f"Best signal: {weekly_stats.get('best_signal', 'N/A')}\n"
        f"Avg RR: {weekly_stats.get('avg_rr', 0)}"
    )

    # Twitter thread
    twitter_prompt = f"""
Write a Twitter/X thread (3 tweets) about our crypto signal performance this week.
Stats: {stats_text}
Rules: honest, no guaranteed profit claims, educational tone, end with risk disclaimer.
Format: Tweet 1: ... Tweet 2: ... Tweet 3: ...
"""
    twitter = llm.invoke(twitter_prompt).content

    # YouTube short script
    youtube_prompt = f"""
Write a 60-second YouTube Shorts script about our best crypto signal this week.
Stats: {stats_text}
Best signal: {weekly_stats.get('best_signal', 'N/A')}
Tone: educational, transparent, beginner-friendly.
Include: what the signal was, why we sent it, what happened.
End with risk disclaimer.
"""
    youtube = llm.invoke(youtube_prompt).content

    print("Agent 6: Content generated.\n")
    return {
        "twitter_thread": twitter,
        "youtube_script": youtube
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test daily recap with sample data
    sample_records = [
        {"pair": "BTCUSDT", "direction": "LONG",  "result": "win"},
        {"pair": "ETHUSDT", "direction": "SHORT", "result": "loss"},
        {"pair": "SOLUSDT", "direction": "LONG",  "result": "pending"},
    ]

    recap = generate_daily_recap(sample_records)
    print("=== DAILY RECAP ===")
    print(recap)

    print("\n=== WEEKLY CONTENT ===")
    weekly = generate_weekly_content({
        "total_signals": 12,
        "win_rate": 67,
        "best_signal": "BTC LONG breakout +4.2%",
        "avg_rr": 2.1
    })
    print("Twitter Thread:")
    print(weekly["twitter_thread"])