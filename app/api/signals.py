# app/api/signals.py
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.signal import ApproveRequest
from app.core.database import (
    save_signal, get_all_signals, get_signal_by_thread,
    save_pending_signal, get_pending_signal,
    get_all_pending_signals, delete_pending_signal
)
from app.graph import build_graph
from app.signal_state import SignalState

router = APIRouter(prefix="/signals", tags=["signals"])


async def run_pipeline(thread_id: str, market_data: dict = None):
    """Runs LangGraph pipeline in background"""
    print(f"\n🚀 Pipeline starting — thread_id: {thread_id}")
    try:
        graph         = build_graph()
        initial_state: SignalState = {
            "market_data":            market_data or {},
            "research_summary":       "",
            "candidate_signal":       {},
            "human_approved":         None,
            "human_feedback":         None,
            "final_whatsapp_message": "",
            "compliance_passed":      False,
            "delivery_status":        "pending",
            "performance_log":        {}
        }
        config      = {"configurable": {"thread_id": thread_id}}
        final_state = graph.invoke(initial_state, config=config)
        save_signal(thread_id, final_state)

        # If signal needs approval → save to DB
        signal = final_state.get("candidate_signal", {})
        if (signal.get("direction") not in ["NO_TRADE", None]
                and final_state.get("delivery_status") == "pending"):
            save_pending_signal(thread_id, final_state, signal)
            print(f"⏳ Signal saved to DB pending — {thread_id}")
        else:
            print(f"✅ Pipeline complete — {final_state['delivery_status']}")

        return final_state

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return None


@router.post("/run")
async def run_signal(background_tasks: BackgroundTasks):
    """Trigger the full signal pipeline"""
    thread_id = str(uuid.uuid4())
    background_tasks.add_task(run_pipeline, thread_id)
    return {
        "message":   "Signal pipeline started",
        "thread_id": thread_id,
        "status":    "running",
        "check_url": f"/signals/{thread_id}"
    }


@router.get("/")
def get_signals():
    """Get all signals from database"""
    signals = get_all_signals()
    return {"total": len(signals), "signals": signals}


@router.get("/pending")
def get_pending():
    """Get signals waiting for human approval"""
    pending = get_all_pending_signals()
    result  = []
    for p in pending:
        signal = p["signal_data"]
        result.append({
            "thread_id":        p["thread_id"],
            "pair":             signal.get("pair"),
            "direction":        signal.get("direction"),
            "confidence":       signal.get("confidence"),
            "setup_type":       signal.get("setup_type"),
            "entry_low":        signal.get("entry_low"),
            "entry_high":       signal.get("entry_high"),
            "stop_loss":        signal.get("stop_loss"),
            "tp1":              signal.get("tp1"),
            "tp2":              signal.get("tp2"),
            "tp3":              signal.get("tp3"),
            "research_summary": p["state"].get("research_summary", "")[:200]
        })
    return {"total_pending": len(result), "pending": result}


@router.get("/{thread_id}")
def get_signal(thread_id: str):
    """Get a specific signal by thread_id"""
    signal = get_signal_by_thread(thread_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@router.post("/approve/{thread_id}")
def approve_signal(thread_id: str, request: ApproveRequest):
    """Approve or reject a pending signal"""
    print(f"🔍 Looking for thread_id: {thread_id}")

    # Get from database instead of memory
    pending = get_pending_signal(thread_id)
    if not pending:
        raise HTTPException(
            status_code=404,
            detail=f"Signal {thread_id} not found."
        )

    state = pending["state"]

    # Build fresh graph and resume
    graph  = build_graph()
    config = {"configurable": {"thread_id": thread_id}}

    updated_state = {
        **state,
        "human_approved": request.approved,
        "human_feedback": request.feedback or (
            "Approved" if request.approved else "Rejected"
        )
    }

    final_state = graph.invoke(updated_state, config=config)
    save_signal(thread_id, final_state)

    # Remove from pending
    delete_pending_signal(thread_id)

    print(f"✅ Signal {thread_id} — {'approved' if request.approved else 'rejected'}")

    return {
        "message":          "Signal processed",
        "thread_id":        thread_id,
        "approved":         request.approved,
        "delivery_status":  final_state["delivery_status"],
        "whatsapp_message": final_state.get("final_whatsapp_message", "")
    }


@router.post("/test-signal")
async def inject_test_signal():
    """Injects a fake signal into pending for testing."""
    thread_id = str(uuid.uuid4())

    fake_state: SignalState = {
        "market_data":            {},
        "research_summary":       "BTC showing strong breakout above resistance with high volume confirmation. Bullish momentum building.",
        "candidate_signal": {
            "pair":          "BTCUSDT",
            "coin":          "BTC",
            "direction":     "LONG",
            "entry_low":     66000.0,
            "entry_high":    66300.0,
            "stop_loss":     65000.0,
            "tp1":           67500.0,
            "tp2":           68500.0,
            "tp3":           70000.0,
            "confidence":    78,
            "risk_score":    2,
            "setup_type":    "breakout",
            "timeframe":     "1h",
            "raw_rationale": "BTC broke above 20-period high with volume confirmation."
        },
        "human_approved":         None,
        "human_feedback":         None,
        "final_whatsapp_message": "",
        "compliance_passed":      False,
        "delivery_status":        "pending",
        "performance_log":        {}
    }

    signal_data = fake_state["candidate_signal"]
    save_pending_signal(thread_id, fake_state, signal_data)

    print(f"✅ Test signal saved to DB: {thread_id}")

    return {
        "message":   "Test signal injected into database",
        "thread_id": thread_id
    }
@router.get("/model/status")
def get_model_status():
    """Get current active model"""
    from app.core.llm import get_active_model_name
    from app.core.config import settings
    return {
        "active_model": settings.ACTIVE_MODEL,
        "model_name":   get_active_model_name()
    }


@router.post("/model/switch/{model}")
def switch_model(model: str):
    """
    Switch between models at runtime.
    model: 'gemini' or 'ollama'
    """
    if model not in ["gemini", "ollama"]:
        raise HTTPException(
            status_code=400,
            detail="Model must be 'gemini' or 'ollama'"
        )
    from app.core.config import settings
    settings.ACTIVE_MODEL = model
    from app.core.llm import get_active_model_name
    return {
        "message":    f"Switched to {model}",
        "model_name": get_active_model_name()
    }