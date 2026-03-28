# main.py
import uuid
import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv


from app.database import init_db, save_signal, get_all_signals, get_signal_by_thread, add_subscriber, get_subscribers
from app.graph import build_graph
from app.signal_state import SignalState

# Add this to your existing imports in main.py
from fastapi import Request
from app.whatsapp import send_message, broadcast_signal, parse_incoming_message, verify_webhook
from app.database import get_subscribers

load_dotenv()

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AlphaPing API",
    description="WhatsApp-First Crypto Signal Copilot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
async def startup():
    init_db()
    print("✅ AlphaPing API started")

# ── Request models ────────────────────────────────────────────────────────────
class ApproveRequest(BaseModel):
    approved: bool
    feedback: str = ""

class SubscriberRequest(BaseModel):
    phone: str
    plan: str = "free"

# ── In-memory pending signals store ──────────────────────────────────────────
# (will move to Redis later)
pending_signals = {}

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "AlphaPing API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/run-signal",
            "/signals",
            "/signals/{thread_id}",
            "/approve/{thread_id}",
            "/pending",
            "/subscribers",
            "/broadcast",
            "/webhook/whatsapp",
            "/health",
            "/docs"
        ]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "AlphaPing"}


@app.post("/run-signal")
async def run_signal(background_tasks: BackgroundTasks):
    """
    Triggers the full signal pipeline.
    Runs in background — returns thread_id immediately.
    Check /signals/{thread_id} for result.
    """
    thread_id = str(uuid.uuid4())

    background_tasks.add_task(run_pipeline, thread_id)

    return {
        "message": "Signal pipeline started",
        "thread_id": thread_id,
        "status": "running",
        "check_url": f"/signals/{thread_id}"
    }
# Note: The actual pipeline logic is in run_pipeline, which is called in the background.


async def run_pipeline(thread_id: str):
    """Runs the LangGraph pipeline in background"""
    print(f"\n🚀 Pipeline started — thread_id: {thread_id}")

    try:
        graph = build_graph()

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

        config = {"configurable": {"thread_id": thread_id}}
        final_state = graph.invoke(initial_state, config=config)

        # Save to database
        save_signal(thread_id, final_state)

        # If signal needs human approval — store in pending
        if final_state.get("delivery_status") == "pending":
            pending_signals[thread_id] = {
                "state": final_state,
                "config": config,
                "graph": graph
            }
            print(f"⏳ Signal pending approval — thread_id: {thread_id}")
        else:
            print(f"✅ Pipeline complete — status: {final_state['delivery_status']}")

    except Exception as e:
        print(f"❌ Pipeline error: {e}")


@app.get("/signals")
def get_signals():
    """Get all signals from database"""
    signals = get_all_signals()
    return {
        "total": len(signals),
        "signals": signals
    }


@app.get("/signals/{thread_id}")
def get_signal(thread_id: str):
    """Get a specific signal by thread_id"""
    signal = get_signal_by_thread(thread_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@app.post("/approve/{thread_id}")
def approve_signal(thread_id: str, request: ApproveRequest):
    """
    Approve or reject a pending signal.
    This is what the admin dashboard will call.
    """
    if thread_id not in pending_signals:
        raise HTTPException(
            status_code=404,
            detail="Signal not found or already processed"
        )

    pending = pending_signals[thread_id]
    state   = pending["state"]
    config  = pending["config"]
    graph   = pending["graph"]

    # Update state with human decision
    updated_state = {
        **state,
        "human_approved": request.approved,
        "human_feedback": request.feedback or ("Approved" if request.approved else "Rejected")
    }

    # Resume the graph
    final_state = graph.invoke(updated_state, config=config)

    # Save to database
    save_signal(thread_id, final_state)

    # Remove from pending
    del pending_signals[thread_id]

    return {
        "message": "Signal processed",
        "thread_id": thread_id,
        "approved": request.approved,
        "delivery_status": final_state["delivery_status"],
        "whatsapp_message": final_state.get("final_whatsapp_message", "")
    }


@app.get("/pending")
def get_pending():
    """Get all signals waiting for human approval"""
    result = []
    for thread_id, data in pending_signals.items():
        signal = data["state"].get("candidate_signal", {})
        result.append({
            "thread_id": thread_id,
            "pair": signal.get("pair"),
            "direction": signal.get("direction"),
            "confidence": signal.get("confidence"),
            "setup_type": signal.get("setup_type"),
            "research_summary": data["state"].get("research_summary", "")[:200]
        })
    return {
        "total_pending": len(result),
        "pending": result
    }


@app.post("/subscribers")
def add_subscriber_route(request: SubscriberRequest):
    """Add a new subscriber"""
    add_subscriber(request.phone, request.plan)
    return {
        "message": "Subscriber added",
        "phone": request.phone,
        "plan": request.plan
    }

# ── WhatsApp Webhook ──────────────────────────────────────────────────────────

@app.get("/webhook/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    """
    Meta calls this to verify our webhook URL.
    Only needed once during WhatsApp Business setup.
    """
    params = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    result = verify_webhook(mode, token, challenge)
    if result:
        return int(result)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook/whatsapp")
async def receive_whatsapp_message(request: Request):
    """
    Receives incoming WhatsApp messages from users.
    Handles: JOIN, STOP, DETAILS, PLAN, HELP + AI responses
    """
    body = await request.json()
    incoming = parse_incoming_message(body)

    if not incoming:
        return {"status": "no_message"}

    from_number = incoming["from"]
    user_message = incoming["message"]

    print(f"📩 Message from {from_number}: {user_message}")

    # Handle with support agent
    from app.agents.support_agent import support_agent
    reply = support_agent(user_message)

    # Send reply back
    send_message(from_number, reply)

    return {"status": "replied"}


@app.post("/broadcast")
async def broadcast_to_subscribers(request: Request):
    """
    Send a message to all active subscribers.
    Used for daily recaps and signal broadcasts.
    """
    body = await request.json()
    message = body.get("message")

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    subscribers = get_subscribers(active=True)
    result = broadcast_signal(message, subscribers)

    return {
        "status": "broadcast_complete",
        "result": result
    }


@app.get("/subscribers")
def get_subscribers_route(plan: str = None):
    """Get all subscribers"""
    subs = get_subscribers(plan=plan)
    return {
        "total": len(subs),
        "subscribers": subs
    }