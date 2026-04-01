# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.router import router

app = FastAPI(
    title=settings.APP_NAME,
    description="WhatsApp-First Crypto Signal Copilot",
    version=settings.APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name":    settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status":  "running",
        "docs":    "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.APP_NAME}


@app.on_event("startup")
async def startup():
    init_db()
    from app.services.signal_service import start_signal_service
    from app.services.websocket_service import start_websocket_streams
    from scripts.scheduler import start_scheduler
    import asyncio
    start_signal_service()
    asyncio.ensure_future(start_websocket_streams())
    start_scheduler()
    print(f"✅ {settings.APP_NAME} API started")