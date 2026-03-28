# app/market_data.py
import os
import asyncio
from pycoingecko import CoinGeckoAPI
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
cg = CoinGeckoAPI(api_key=os.getenv("COINGECKO_API_KEY"))
binance_client = Client(
    api_key=os.getenv("BINANCE_API_KEY"),
    api_secret=os.getenv("BINANCE_SECRET")
)

# Pairs we track
PAIRS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT"
}

def get_live_prices():
    """Get current prices from Binance for BTC, ETH, SOL"""
    prices = {}
    for name, symbol in PAIRS.items():
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
        prices[name] = float(ticker["price"])
    return prices

def get_klines(symbol: str, interval: str = "1h", limit: int = 50):
    """
    Get candlestick data (OHLCV) from Binance
    interval options: "1m", "5m", "15m", "1h", "4h", "1d"
    """
    raw = binance_client.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit
    )
    candles = []
    for k in raw:
        candles.append({
            "open_time": k[0],
            "open":  float(k[1]),
            "high":  float(k[2]),
            "low":   float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return candles

def get_market_snapshot():
    """
    Full market snapshot for all 3 pairs.
    This is what gets passed into SignalState as market_data.
    """
    snapshot = {}
    for name, symbol in PAIRS.items():
        candles = get_klines(symbol, interval="1h", limit=50)
        latest = candles[-1]
        prev    = candles[-2]

        # Volume comparison
        avg_volume = sum(c["volume"] for c in candles[:-1]) / len(candles[:-1])
        volume_ratio = latest["volume"] / avg_volume if avg_volume > 0 else 1.0

        snapshot[name] = {
            "symbol": symbol,
            "price": latest["close"],
            "open": latest["open"],
            "high": latest["high"],
            "low": latest["low"],
            "volume": latest["volume"],
            "volume_ratio": round(volume_ratio, 2),  # >1.5 = high volume
            "price_change_pct": round(
                ((latest["close"] - prev["close"]) / prev["close"]) * 100, 2
            ),
            "candles": candles  # full history for strategy rules
        }
    return snapshot


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching live market data...\n")
    snapshot = get_market_snapshot()
    for coin, data in snapshot.items():
        print(f"{coin}:")
        print(f"  Price:         ${data['price']:,.2f}")
        print(f"  Change (1h):   {data['price_change_pct']}%")
        print(f"  Volume ratio:  {data['volume_ratio']}x avg")
        print()