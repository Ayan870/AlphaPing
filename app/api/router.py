# app/api/router.py
from fastapi import APIRouter
from app.api import signals, subscribers, webhook

router = APIRouter()

router.include_router(signals.router)
router.include_router(subscribers.router)
router.include_router(webhook.router)