# app/services/websocket_service.py
import asyncio
import json
import websockets
from datetime import datetime
from app.core.config import settings

# Store latest candle data for each pair
# This is shared memory — signal service reads from here
latest_candles = {
    "BTCUSDT": [],
    "ETHUSDT": [],
    "SOLUSDT": []
}

# Store latest closed candle for each pair
latest_closed_candle = {
    "BTCUSDT": None,
    "ETHUSDT": None,
    "SOLUSDT": None
}

# Callback function — called when a candle closes
# Signal service will register itself here
on_candle_close_callback = None


def set_candle_close_callback(callback):
    """
    Register a callback function that fires when a candle closes.
    Signal service calls this to hook into the WebSocket.
    """
    global on_candle_close_callback
    on_candle_close_callback = callback
    print("✅ Candle close callback registered")


async def handle_candle_message(symbol: str, message: dict):
    """
    Processes each candle message from Binance WebSocket.
    Only acts when candle is CLOSED (is_closed = True).
    """
    candle = message.get("k", {})

    # Parse candle data
    candle_data = {
        "symbol":     symbol,
        "open_time":  candle.get("t"),
        "open":       float(candle.get("o", 0)),
        "high":       float(candle.get("h", 0)),
        "low":        float(candle.get("l", 0)),
        "close":      float(candle.get("c", 0)),
        "volume":     float(candle.get("v", 0)),
        "is_closed":  candle.get("x", False),
        "closed_at":  datetime.now().isoformat()
    }

    # Always update latest price (even on open candles)
    if symbol in latest_candles:
        # Keep last 50 candles max
        latest_candles[symbol].append(candle_data)
        if len(latest_candles[symbol]) > 50:
            latest_candles[symbol].pop(0)

    # Only trigger signal check when candle CLOSES
    if candle_data["is_closed"]:
        latest_closed_candle[symbol] = candle_data

        print(f"\n🕯️  Candle closed: {symbol}")
        print(f"   Close: ${candle_data['close']:,.2f}")
        print(f"   Volume: {candle_data['volume']:,.0f}")
        print(f"   Time: {candle_data['closed_at']}")

        # Fire the callback → signal service checks for setups
        if on_candle_close_callback:
            await on_candle_close_callback(symbol, candle_data)


async def stream_symbol(symbol: str):
    """
    Opens a WebSocket connection for one symbol.
    Reconnects automatically if connection drops.
    """
    # Binance WebSocket URL for 1h kline stream
    url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_1h"

    while True:  # auto-reconnect loop
        try:
            print(f"🔌 Connecting to Binance WebSocket: {symbol}...")
            async with websockets.connect(url) as ws:
                print(f"✅ Connected: {symbol}")
                async for message in ws:
                    data = json.loads(message)
                    await handle_candle_message(symbol, data)

        except websockets.exceptions.ConnectionClosed:
            print(f"⚠️  Connection closed for {symbol} — reconnecting in 5s...")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ WebSocket error for {symbol}: {e}")
            print(f"   Reconnecting in 10s...")
            await asyncio.sleep(10)


async def start_websocket_streams():
    """
    Starts WebSocket streams for ALL pairs simultaneously.
    Runs forever in the background.
    """
    symbols = list(settings.PAIRS.values())  # BTCUSDT, ETHUSDT, SOLUSDT
    print(f"\n🚀 Starting WebSocket streams for: {symbols}")

    # Run all streams concurrently
    await asyncio.gather(*[stream_symbol(symbol) for symbol in symbols])


def get_latest_price(symbol: str) -> float:
    """Get the latest price for a symbol from WebSocket data"""
    candles = latest_candles.get(symbol, [])
    if candles:
        return candles[-1]["close"]
    return 0.0


def get_latest_candles(symbol: str, limit: int = 50) -> list:
    """Get latest candles for a symbol from WebSocket data"""
    candles = latest_candles.get(symbol, [])
    return candles[-limit:] if len(candles) > limit else candles


# ── Quick test ────────────────────────────────────────────────────────────────
async def test_callback(symbol: str, candle: dict):
    """Test callback — just prints when candle closes"""
    print(f"\n🎯 TEST CALLBACK FIRED for {symbol}")
    print(f"   This is where signal service will check for setups")


async def main():
    """Test the WebSocket service"""
    print("Testing WebSocket service...")
    print("Will show live BTC/ETH/SOL candle data")
    print("Press Ctrl+C to stop\n")

    # Register test callback
    set_candle_close_callback(test_callback)

    # Start streams
    await start_websocket_streams()


if __name__ == "__main__":
    asyncio.run(main())