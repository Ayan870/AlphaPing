# app/api/subscribers.py
from fastapi import APIRouter, HTTPException
from app.schemas.subscriber import SubscriberRequest, BroadcastRequest
from app.core.database import add_subscriber, get_subscribers
from app.whatsapp import broadcast_signal

router = APIRouter(prefix="/subscribers", tags=["subscribers"])


@router.post("/")
def add_subscriber_route(request: SubscriberRequest):
    """Add a new subscriber"""
    add_subscriber(request.phone, request.plan)
    return {
        "message": "Subscriber added",
        "phone":   request.phone,
        "plan":    request.plan
    }


@router.get("/")
def get_subscribers_route(plan: str = None):
    """Get all subscribers"""
    subs = get_subscribers(plan=plan)
    return {"total": len(subs), "subscribers": subs}