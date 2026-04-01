# app/schemas/signal.py
from pydantic import BaseModel
from typing import Optional

class ApproveRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = ""

class SignalResponse(BaseModel):
    thread_id: str
    pair: Optional[str]
    direction: Optional[str]
    confidence: Optional[int]
    delivery_status: str