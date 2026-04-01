# app/schemas/subscriber.py
from pydantic import BaseModel
from typing import Optional

class SubscriberRequest(BaseModel):
    phone: str
    plan: Optional[str] = "free"

class BroadcastRequest(BaseModel):
    message: str