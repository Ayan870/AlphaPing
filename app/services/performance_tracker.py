# app/services/performance_tracker.py
import asyncio
import json
from datetime import datetime
from app.core.database import get_connection


def get_active_signals():
    """Get all sent signals that are still pending result"""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM signals 
        WHERE delivery_status = 'sent'
        AND json_extract(performance_log, '$.result') = 'pending'
        AND tp1 IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_performance(signal_id: int, updates: dict):
    """Update performance log for a signal"""
    conn   = get_connection()
    cursor = conn.cursor()

    # Get current performance log
    cursor.execute(
        "SELECT performance_log FROM signals WHERE id = ?",
        (signal_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return

    current_log = json.loads(row["performance_log"] or "{}")
    current_log.update(updates)
    current_log["updated_at"] = datetime.now().isoformat()

    cursor.execute("""
        UPDATE signals 
        SET performance_log = ?, updated_at = ?
        WHERE id = ?
    """, (json.dumps(current_log), datetime.now().isoformat(), signal_id))

    conn.commit()
    conn.close()
    print(f"📊 Performance updated for signal {signal_id}: {updates}")


def check_signal_levels(signal: dict, current_price: float) -> dict:
    """
    Check if current price has hit any TP or SL levels.
    Returns dict of updates to apply.
    """
    perf_log = json.loads(signal.get("performance_log") or "{}")
    updates  = {}
    result   = perf_log.get("result", "pending")

    # Skip if already closed
    if result in ["win", "loss", "partial"]:
        return {}

    direction = signal.get("direction")
    tp1       = signal.get("tp1")
    tp2       = signal.get("tp2")
    tp3       = signal.get("tp3")
    sl        = signal.get("stop_loss")
    entry     = signal.get("entry_low", 0)

    if direction == "LONG":
        # Check Stop Loss
        if sl and current_price <= sl and not perf_log.get("sl_hit"):
            updates["sl_hit"]   = True
            updates["result"]   = "loss"
            updates["final_pnl"] = round(((sl - entry) / entry) * 100, 2)
            print(f"❌ SL HIT for signal {signal['id']} — Price: ${current_price}")

        # Check Take Profits
        elif tp1 and current_price >= tp1 and not perf_log.get("tp1_hit"):
            updates["tp1_hit"] = True
            updates["result"]  = "partial"
            updates["final_pnl"] = round(((tp1 - entry) / entry) * 100, 2)
            print(f"✅ TP1 HIT for signal {signal['id']} — Price: ${current_price}")

        elif tp2 and current_price >= tp2 and not perf_log.get("tp2_hit"):
            updates["tp2_hit"] = True
            updates["result"]  = "partial"
            updates["final_pnl"] = round(((tp2 - entry) / entry) * 100, 2)
            print(f"✅ TP2 HIT for signal {signal['id']} — Price: ${current_price}")

        elif tp3 and current_price >= tp3 and not perf_log.get("tp3_hit"):
            updates["tp3_hit"] = True
            updates["result"]  = "win"
            updates["final_pnl"] = round(((tp3 - entry) / entry) * 100, 2)
            print(f"🎯 TP3 HIT for signal {signal['id']} — Price: ${current_price}")

    elif direction == "SHORT":
        # Check Stop Loss
        if sl and current_price >= sl and not perf_log.get("sl_hit"):
            updates["sl_hit"]    = True
            updates["result"]    = "loss"
            updates["final_pnl"] = round(((entry - sl) / entry) * 100, 2) * -1
            print(f"❌ SL HIT for signal {signal['id']} — Price: ${current_price}")

        # Check Take Profits
        elif tp1 and current_price <= tp1 and not perf_log.get("tp1_hit"):
            updates["tp1_hit"]   = True
            updates["result"]    = "partial"
            updates["final_pnl"] = round(((entry - tp1) / entry) * 100, 2)
            print(f"✅ TP1 HIT for signal {signal['id']} — Price: ${current_price}")

        elif tp2 and current_price <= tp2 and not perf_log.get("tp2_hit"):
            updates["tp2_hit"]   = True
            updates["result"]    = "partial"
            updates["final_pnl"] = round(((entry - tp2) / entry) * 100, 2)
            print(f"✅ TP2 HIT for signal {signal['id']} — Price: ${current_price}")

        elif tp3 and current_price <= tp3 and not perf_log.get("tp3_hit"):
            updates["tp3_hit"]   = True
            updates["result"]    = "win"
            updates["final_pnl"] = round(((entry - tp3) / entry) * 100, 2)
            print(f"🎯 TP3 HIT for signal {signal['id']} — Price: ${current_price}")

    return updates


async def track_active_signals():
    """
    Background task that monitors active signals.
    Runs every 30 seconds and checks current prices.
    """
    print("📊 Performance tracker started")

    while True:
        try:
            active_signals = get_active_signals()

            if active_signals:
                print(f"👀 Watching {len(active_signals)} active signal(s)...")

                # Get current prices from WebSocket data
                from app.services.websocket_service import get_latest_price

                for signal in active_signals:
                    pair          = signal.get("pair")
                    current_price = get_latest_price(pair)

                    if current_price == 0:
                        continue

                    updates = check_signal_levels(signal, current_price)
                    if updates:
                        update_performance(signal["id"], updates)

                        # Send WhatsApp notification
                        result = updates.get("result", "")
                        if result in ["win", "loss", "partial"]:
                            await notify_result(signal, updates, current_price)

        except Exception as e:
            print(f"❌ Performance tracker error: {e}")

        await asyncio.sleep(30)  # Check every 30 seconds


async def notify_result(signal: dict, updates: dict, current_price: float):
    """Send WhatsApp notification when TP/SL is hit"""
    try:
        from app.whatsapp import broadcast_signal
        from app.core.database import get_subscribers

        result  = updates.get("result", "pending")
        pnl     = updates.get("final_pnl", 0)
        pair    = signal.get("pair", "")

        if updates.get("sl_hit"):
            emoji   = "❌"
            outcome = "STOP LOSS HIT"
        elif updates.get("tp3_hit"):
            emoji   = "🎯"
            outcome = "TP3 HIT — FULL TARGET"
        elif updates.get("tp2_hit"):
            emoji   = "✅"
            outcome = "TP2 HIT"
        elif updates.get("tp1_hit"):
            emoji   = "✅"
            outcome = "TP1 HIT"
        else:
            return

        message = (
            f"{emoji} *{pair} Signal Update*\n\n"
            f"*Result:* {outcome}\n"
            f"*Current Price:* ${current_price:,.2f}\n"
            f"*PnL:* {'+' if pnl > 0 else ''}{pnl}%\n\n"
            f"⚠️ _Not financial advice. Trade responsibly._"
        )

        subscribers = get_subscribers(active=True)
        if subscribers:
            broadcast_signal(message, subscribers)
            print(f"📱 Result notification sent: {outcome}")

    except Exception as e:
        print(f"❌ Notification error: {e}")


def start_performance_tracker():
    """Start the performance tracker as background task"""
    asyncio.ensure_future(track_active_signals())
    print("✅ Performance tracker started")