# scripts/scheduler.py
import asyncio
import uuid
from datetime import datetime, date
from app.core.config import settings
from app.core.database import save_signal
from app.services.signal_service import run_pipeline, can_send_signal


async def run_scheduled_pipeline():
    """
    Backup pipeline run.
    Called every hour in case WebSocket missed a candle close.
    Uses REST API (market_data.py) instead of WebSocket data.
    """
    print(f"\n⏰ Scheduler triggered at {datetime.now().strftime('%H:%M:%S')}")

    # Check daily limit
    if not can_send_signal():
        print(f"⛔ Daily limit reached. Skipping scheduled run.")
        return

    # Use REST API as backup data source
    try:
        from app.market_data import get_market_snapshot
        market_data = get_market_snapshot()
        thread_id   = f"scheduled-{str(uuid.uuid4())}"

        print(f"📡 Running backup pipeline — thread_id: {thread_id}")
        await run_pipeline(thread_id, market_data)

    except Exception as e:
        print(f"❌ Scheduler error: {e}")


async def run_daily_recap():
    """
    Runs daily recap at 8pm.
    Fetches today's signals and broadcasts summary to subscribers.
    """
    print(f"\n📊 Running daily recap...")

    try:
        from app.core.database import get_all_signals
        from app.agents.growth_agent import generate_daily_recap
        from app.whatsapp import broadcast_signal
        from app.core.database import get_subscribers

        # Get today's signals
        all_signals = get_all_signals()
        today       = date.today().isoformat()
        today_signals = [
            s for s in all_signals
            if s.get("created_at", "").startswith(today)
            and s.get("delivery_status") == "sent"
        ]

        # Build performance records
        records = []
        for s in today_signals:
            records.append({
                "pair":      s.get("pair", "N/A"),
                "direction": s.get("direction", "N/A"),
                "result":    "pending"
            })

        # Generate recap message
        recap = generate_daily_recap(records)
        print(f"📝 Recap generated:\n{recap[:100]}...")

        # Broadcast to all subscribers
        subscribers = get_subscribers(active=True)
        if subscribers:
            result = broadcast_signal(recap, subscribers)
            print(f"📤 Recap sent to {result['sent']} subscribers")
        else:
            print("⚠️  No active subscribers yet")

    except Exception as e:
        print(f"❌ Daily recap error: {e}")


async def scheduler_loop():
    """
    Main scheduler loop.
    Runs backup pipeline every hour.
    Runs daily recap at 8pm.
    """
    print("⏰ Scheduler started")
    print(f"   Backup pipeline: every 1 hour")
    print(f"   Daily recap:     every day at 20:00\n")

    while True:
        now = datetime.now()

        # Run backup pipeline every hour at :55 minutes
        # (5 min after candle close to avoid duplicate with WebSocket)
        if now.minute == 55:
            await run_scheduled_pipeline()

        # Run daily recap at 8:00pm
        if now.hour == 20 and now.minute == 0:
            await run_daily_recap()

        # Check every minute
        await asyncio.sleep(60)


def start_scheduler():
    """Start the scheduler as background task"""
    asyncio.ensure_future(scheduler_loop())
    print("✅ Scheduler started")


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def test():
        print("Testing scheduler components...\n")

        print("1. Testing backup pipeline...")
        await run_scheduled_pipeline()

        print("\n2. Testing daily recap...")
        await run_daily_recap()

    asyncio.run(test())