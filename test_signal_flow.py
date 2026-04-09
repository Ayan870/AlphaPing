# test_signal_flow.py
# Complete end-to-end test without needing /docs
import requests
import time

API = "http://localhost:8000"

def run_test():
    print("🚀 AlphaPing Signal Flow Test")
    print("="*40)

    # Step 1 — Inject test signal
    print("\n1. Injecting test signal...")
    res = requests.post(f"{API}/signals/test-signal/BTCUSDT")
    data = res.json()
    thread_id = data["thread_id"]
    print(f"✅ Signal injected: {thread_id}")

    # Step 2 — Wait 2 seconds
    print("\n2. Waiting 2 seconds...")
    time.sleep(2)

    # Step 3 — Approve signal
    print("\n3. Approving signal...")
    res = requests.post(
        f"{API}/signals/approve/{thread_id}",
        json={"approved": True, "feedback": "Test approval"}
    )
    data = res.json()
    print(f"✅ Status: {data.get('delivery_status')}")

    # Step 4 — Result
    print("\n4. Waiting for Ollama to format message (~30 seconds)...")
    print("   Check your WhatsApp!")
    print("\n" + "="*40)
    print("✅ Test complete")

if __name__ == "__main__":
    run_test()