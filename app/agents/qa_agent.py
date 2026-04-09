# app/agents/qa_agent.py
from app.signal_state import SignalState

# ── Strategy Rules ───────────────────────────────────────────────────────────

def check_breakout(candles: list) -> dict:
    """
    Breakout setup:
    Price closes above the highest high of last 20 candles
    with volume > 1.5x average
    """
    if len(candles) < 22:
        return {"detected": False}

    recent    = candles[-1]
    lookback  = candles[-22:-2]  # 20 candles before current

    highest_high = max(c["high"] for c in lookback)
    avg_volume   = sum(c["volume"] for c in lookback) / len(lookback)
    volume_ratio = recent["volume"] / avg_volume if avg_volume > 0 else 0

    if recent["close"] > highest_high and volume_ratio > 1.5:
        return {
            "detected": True,
            "setup_type": "breakout",
            "confidence_bonus": 20,
            "entry_low":  highest_high,
            "entry_high": highest_high * 1.002,  # 0.2% above breakout
            "stop_loss":  highest_high * 0.985,  # 1.5% below breakout
            "tp1": highest_high * 1.02,
            "tp2": highest_high * 1.04,
            "tp3": highest_high * 1.07,
            "direction": "LONG"
        }
    return {"detected": False}


def check_volume_surge(candles: list) -> dict:
    """
    Volume Surge setup:
    Volume is 2x+ average AND price moved > 1% in same direction
    """
    if len(candles) < 20:
        return {"detected": False}

    recent   = candles[-1]
    lookback = candles[-21:-1]

    avg_volume   = sum(c["volume"] for c in lookback) / len(lookback)
    volume_ratio = recent["volume"] / avg_volume if avg_volume > 0 else 0
    price_change = ((recent["close"] - recent["open"]) / recent["open"]) * 100

    if volume_ratio > 2.0 and abs(price_change) > 1.0:
        direction = "LONG" if price_change > 0 else "SHORT"
        entry     = recent["close"]
        sl_pct    = 0.02  # 2% stop loss
        return {
            "detected": True,
            "setup_type": "volume_surge",
            "confidence_bonus": 15,
            "entry_low":  entry * 0.999,
            "entry_high": entry * 1.001,
            "stop_loss":  entry * (1 - sl_pct) if direction == "LONG" else entry * (1 + sl_pct),
            "tp1": entry * 1.015 if direction == "LONG" else entry * 0.985,
            "tp2": entry * 1.03  if direction == "LONG" else entry * 0.97,
            "tp3": entry * 1.05  if direction == "LONG" else entry * 0.95,
            "direction": direction
        }
    return {"detected": False}


def check_support_bounce(candles: list) -> dict:
    """
    Support Bounce setup:
    Price touches 20-period low and bounces back up > 0.5%
    """
    if len(candles) < 22:
        return {"detected": False}

    recent   = candles[-1]
    lookback = candles[-22:-2]

    lowest_low   = min(c["low"] for c in lookback)
    bounce_pct   = ((recent["close"] - recent["low"]) / recent["low"]) * 100
    near_support = recent["low"] <= lowest_low * 1.005  # within 0.5% of support

    if near_support and bounce_pct > 0.5:
        entry = recent["close"]
        return {
            "detected": True,
            "setup_type": "support_bounce",
            "confidence_bonus": 10,
            "entry_low":  entry * 0.999,
            "entry_high": entry * 1.001,
            "stop_loss":  lowest_low * 0.99,
            "tp1": entry * 1.015,
            "tp2": entry * 1.03,
            "tp3": entry * 1.05,
            "direction": "LONG"
        }
    return {"detected": False}


# ── Base Confidence Score ─────────────────────────────────────────────────────

def calculate_base_confidence(data: dict) -> int:
    """
    Start at 50, add/subtract based on market conditions
    """
    score = 50

    # Volume activity
    if data["volume_ratio"] > 2.0:
        score += 15
    elif data["volume_ratio"] > 1.5:
        score += 10
    elif data["volume_ratio"] < 0.5:
        score -= 10

    # Price momentum
    change = abs(data["price_change_pct"])
    if change > 2.0:
        score += 10
    elif change > 1.0:
        score += 5
    elif change < 0.1:
        score -= 5

    return min(max(score, 0), 100)  # clamp 0-100


# ── Main QA Agent ─────────────────────────────────────────────────────────────

def qa_agent(state: SignalState) -> SignalState:
    """
    Agent 2 — Signal QA
    - Runs strategy rules on each pair
    - Scores confidence
    - Returns best candidate signal or NO_TRADE
    """
    print("Agent 2: Running strategy rules...")

    market_data = state["market_data"]
    best_signal = None
    best_confidence = 0

    strategies = [check_breakout, check_volume_surge, check_support_bounce]

    for coin, data in market_data.items():
        candles = data["candles"]
        base_confidence = calculate_base_confidence(data)

        for strategy in strategies:
            result = strategy(candles)
            if result["detected"]:
                confidence = min(base_confidence + result["confidence_bonus"], 100)
                print(f"  {coin}: {result['setup_type']} detected — confidence {confidence}")

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_signal = {
                        "pair": data["symbol"],
                        "coin": coin,
                        "direction": result["direction"],
                        "entry_low":  round(result["entry_low"], 4),
                        "entry_high": round(result["entry_high"], 4),
                        "stop_loss":  round(result["stop_loss"], 4),
                        "tp1": round(result["tp1"], 4),
                        "tp2": round(result["tp2"], 4),
                        "tp3": round(result["tp3"], 4),
                        "confidence": confidence,
                        "risk_score": 5 - min(confidence // 20, 4),
                        "setup_type": result["setup_type"],
                        "timeframe": "1h",
                        "raw_rationale": state["research_summary"]
                    }

    # If no setup found or confidence too low → NO_TRADE
    if best_signal is None or best_confidence < 60:
        print("  No valid setup found → NO_TRADE\n")
        candidate = {
            "direction": "NO_TRADE",
            "confidence": best_confidence,
            "reason": "No setup met minimum confidence threshold"
        }
    else:
        print(f"  Best signal: {best_signal['coin']} {best_signal['direction']} "
              f"({best_signal['setup_type']}) — confidence {best_signal['confidence']}\n")
        candidate = best_signal

    return {
        **state,
        "candidate_signal": candidate
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from app.market_data import get_market_snapshot

    snapshot = get_market_snapshot()

    initial_state: SignalState = {
        "market_data": snapshot,
        "research_summary": "Test summary",
        "candidate_signal": {},
        "human_approved": None,
        "human_feedback": None,
        "final_whatsapp_message": "",
        "compliance_passed": False,
        "delivery_status": "pending",
        "performance_log": {}
    }

    result = qa_agent(initial_state)
    print("Candidate signal:")
    for k, v in result["candidate_signal"].items():
        if k != "raw_rationale":
            print(f"  {k}: {v}")