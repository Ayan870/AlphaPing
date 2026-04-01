# app/api/webhook.py
from fastapi import APIRouter, HTTPException, Request
from app.whatsapp import (send_message, broadcast_signal,
                           parse_incoming_message, verify_webhook)
from app.core.database import get_subscribers
from app.schemas.subscriber import BroadcastRequest

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    """Meta calls this once to verify webhook URL"""
    params    = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    result = verify_webhook(mode, token, challenge)
    if result:
        return int(result)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def receive_whatsapp_message(request: Request):
    """Receives incoming WhatsApp messages"""
    body     = await request.json()
    incoming = parse_incoming_message(body)

    if not incoming:
        return {"status": "no_message"}

    from_number  = incoming["from"]
    user_message = incoming["message"]
    print(f"📩 Message from {from_number}: {user_message}")

    from app.agents.support_agent import support_agent
    reply = support_agent(user_message)
    send_message(from_number, reply)
    return {"status": "replied"}