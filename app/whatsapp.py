# app/whatsapp.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"
PHONE_NUMBER_ID  = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
ACCESS_TOKEN     = os.getenv("WHATSAPP_ACCESS_TOKEN")
VERIFY_TOKEN     = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")


# ── Send a text message ───────────────────────────────────────────────────────
def send_message(to: str, message: str) -> dict:
    """
    Send a WhatsApp text message to a phone number.
    'to' format: international format without + 
    Example: "923001234567" for Pakistan +92 300 1234567
    """
    if not PHONE_NUMBER_ID or not ACCESS_TOKEN:
        print("⚠️  WhatsApp credentials not set — printing message instead:")
        print(f"TO: {to}")
        print(f"MESSAGE:\n{message}")
        return {"status": "simulated", "to": to}

    url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"✅ WhatsApp message sent to {to}")
        return response.json()
    else:
        print(f"❌ Failed to send message: {response.text}")
        return {"error": response.text}


# ── Send to all subscribers ───────────────────────────────────────────────────
def broadcast_signal(message: str, subscribers: list) -> dict:
    """
    Send a signal message to all active subscribers.
    subscribers = list of dicts with 'phone' key
    """
    results = {
        "total": len(subscribers),
        "sent": 0,
        "failed": 0,
        "details": []
    }

    for sub in subscribers:
        phone = sub.get("phone", "").replace("+", "").replace(" ", "")
        if not phone:
            continue

        result = send_message(phone, message)

        if "error" in result:
            results["failed"] += 1
            results["details"].append({
                "phone": phone,
                "status": "failed",
                "error": result["error"]
            })
        else:
            results["sent"] += 1
            results["details"].append({
                "phone": phone,
                "status": "sent"
            })

    print(f"📤 Broadcast complete: {results['sent']} sent, {results['failed']} failed")
    return results


# ── Handle incoming webhook messages ─────────────────────────────────────────
def parse_incoming_message(webhook_data: dict) -> dict | None:
    """
    Parse incoming WhatsApp webhook payload.
    Returns dict with 'from' and 'message' or None if not a text message.
    """
    try:
        entry    = webhook_data["entry"][0]
        changes  = entry["changes"][0]
        value    = changes["value"]
        messages = value.get("messages", [])

        if not messages:
            return None

        msg = messages[0]

        if msg["type"] != "text":
            return None

        return {
            "from":    msg["from"],           # phone number
            "message": msg["text"]["body"],   # message text
            "msg_id":  msg["id"]              # message ID
        }

    except (KeyError, IndexError):
        return None


# ── Webhook verification ──────────────────────────────────────────────────────
def verify_webhook(mode: str, token: str, challenge: str) -> str | None:
    """
    Verifies the WhatsApp webhook during Meta setup.
    Returns challenge string if valid, None if invalid.
    """
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified")
        return challenge
    print("❌ Webhook verification failed")
    return None


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test without real credentials — simulates sending
    print("Testing WhatsApp module...\n")

    # Test 1 — single message
    result = send_message(
        to="923001234567",
        message=(
            "🟢 *BTCUSDT LONG Signal*\n\n"
            "Entry: $66,000 - $66,300\n"
            "Stop Loss: $65,000\n"
            "TP1: $67,500\n"
            "TP2: $68,500\n"
            "TP3: $70,000\n\n"
            "⚠️ Not financial advice."
        )
    )
    print(f"Result: {result}\n")

    # Test 2 — broadcast
    test_subscribers = [
        {"phone": "+923001234567"},
        {"phone": "+923009876543"},
    ]
    broadcast_result = broadcast_signal(
        "📊 Test broadcast message",
        test_subscribers
    )
    print(f"Broadcast result: {broadcast_result}")