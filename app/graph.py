# app/graph.py
import os
from typing import Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.signal_state import SignalState
from app.agents.research_agent import research_agent
from app.agents.qa_agent import qa_agent
from app.agents.messaging_agent import messaging_agent
from app.agents.compliance_agent import compliance_agent

load_dotenv()

# ── Routing functions ─────────────────────────────────────────────────────────

def route_after_qa(state: SignalState) -> Literal["human_approval", "end_no_trade"]:
    """
    After QA agent:
    - NO_TRADE or low confidence → end immediately
    - Valid signal → go to human approval
    """
    signal = state["candidate_signal"]
    if signal.get("direction") == "NO_TRADE":
        print("Router: NO_TRADE detected → ending pipeline\n")
        return "end_no_trade"
    if signal.get("confidence", 0) < 60:
        print("Router: Confidence too low → ending pipeline\n")
        return "end_no_trade"
    print("Router: Valid signal → sending to human approval\n")
    return "human_approval"


def route_after_compliance(state: SignalState) -> Literal["deliver", "messaging"]:
    """
    After compliance check:
    - Passed → deliver
    - Failed → back to messaging to rewrite
    """
    if state["compliance_passed"]:
        return "deliver"
    print("Router: Compliance failed → rewriting message\n")
    return "messaging"


def route_after_human(state: SignalState) -> Literal["messaging", "end_rejected"]:
    """
    After human approval node:
    - Approved → messaging agent
    - Rejected → end
    """
    if state["human_approved"]:
        print("Router: Signal approved → formatting message\n")
        return "messaging"
    print("Router: Signal rejected → ending pipeline\n")
    return "end_rejected"


# ── Special nodes ─────────────────────────────────────────────────────────────

def human_approval_node(state: SignalState) -> SignalState:
    """
    Human-in-the-loop node.
    In terminal mode: asks you to approve/reject.
    Later: this will pause and wait for admin dashboard input.
    """
    signal = state["candidate_signal"]

    print("\n" + "="*50)
    print("🔔 HUMAN APPROVAL REQUIRED")
    print("="*50)
    print(f"Pair:       {signal.get('pair')}")
    print(f"Direction:  {signal.get('direction')}")
    print(f"Entry:      ${signal.get('entry_low'):,.2f} - ${signal.get('entry_high'):,.2f}")
    print(f"Stop Loss:  ${signal.get('stop_loss'):,.2f}")
    print(f"TP1:        ${signal.get('tp1'):,.2f}")
    print(f"TP2:        ${signal.get('tp2'):,.2f}")
    print(f"TP3:        ${signal.get('tp3'):,.2f}")
    print(f"Confidence: {signal.get('confidence')}/100")
    print(f"Setup:      {signal.get('setup_type')}")
    print(f"\nResearch Summary:\n{state['research_summary']}")
    print("="*50)

    while True:
        decision = input("\nApprove this signal? (y/n): ").strip().lower()
        if decision == "y":
            feedback = input("Any notes? (press Enter to skip): ").strip()
            return {
                **state,
                "human_approved": True,
                "human_feedback": feedback or "Approved"
            }
        elif decision == "n":
            reason = input("Reason for rejection: ").strip()
            return {
                **state,
                "human_approved": False,
                "human_feedback": reason or "Rejected by admin"
            }
        else:
            print("Please type y or n")


def delivery_node(state: SignalState) -> SignalState:
    """
    Delivery node.
    For now: prints the final message to terminal.
    Later: calls WhatsApp Cloud API.
    """
    print("\n" + "="*50)
    print("📤 SIGNAL READY TO DELIVER")
    print("="*50)
    print(state["final_whatsapp_message"])
    print("="*50)
    print("✅ Signal delivered successfully (terminal mode)\n")

    return {
        **state,
        "delivery_status": "sent",
        "performance_log": {
            "sent_at": str(os.popen("date /t").read().strip()),
            "entry_hit": False,
            "tp1_hit": False,
            "tp2_hit": False,
            "tp3_hit": False,
            "sl_hit": False,
            "final_pnl": 0.0,
            "result": "pending"
        }
    }


def end_no_trade_node(state: SignalState) -> SignalState:
    """Called when no valid setup is found"""
    print("Pipeline ended: No trade signal generated.\n")
    return {**state, "delivery_status": "no_trade"}


def end_rejected_node(state: SignalState) -> SignalState:
    """Called when human rejects the signal"""
    print(f"Pipeline ended: Signal rejected. Reason: {state.get('human_feedback')}\n")
    return {**state, "delivery_status": "rejected"}


# ── Build the graph ───────────────────────────────────────────────────────────

def build_graph():
    """
    Builds and compiles the full LangGraph signal pipeline.
    Uses MemorySaver for now (will switch to PostgresSaver later).
    """
    checkpointer = MemorySaver()
    graph = StateGraph(SignalState)

    # Add all nodes
    graph.add_node("research",       research_agent)
    graph.add_node("qa",             qa_agent)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("messaging",      messaging_agent)
    graph.add_node("compliance",     compliance_agent)
    graph.add_node("deliver",        delivery_node)
    graph.add_node("end_no_trade",   end_no_trade_node)
    graph.add_node("end_rejected",   end_rejected_node)

    # Entry point
    graph.set_entry_point("research")

    # Edges
    graph.add_edge("research", "qa")

    # After QA → conditional routing
    graph.add_conditional_edges(
        "qa",
        route_after_qa,
        {
            "human_approval": "human_approval",
            "end_no_trade":   "end_no_trade"
        }
    )

    # After human approval → conditional routing
    graph.add_conditional_edges(
        "human_approval",
        route_after_human,
        {
            "messaging":    "messaging",
            "end_rejected": "end_rejected"
        }
    )

    # After messaging → compliance
    graph.add_edge("messaging", "compliance")

    # After compliance → conditional routing
    graph.add_conditional_edges(
        "compliance",
        route_after_compliance,
        {
            "deliver":  "deliver",
            "messaging": "messaging"
        }
    )

    # End nodes
    graph.add_edge("deliver",      END)
    graph.add_edge("end_no_trade", END)
    graph.add_edge("end_rejected", END)

    return graph.compile(checkpointer=checkpointer)


# ── Run the pipeline ──────────────────────────────────────────────────────────

def run_signal_pipeline():
    """
    Runs the full signal pipeline once.
    This is the main function you call to generate + deliver a signal.
    """
    print("\n" + "="*50)
    print("🚀 AlphaPing Signal Pipeline Starting...")
    print("="*50 + "\n")

    app = build_graph()

    # Initial empty state
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

    # Config needed for checkpointing
    config = {"configurable": {"thread_id": "signal-001"}}

    # Run the graph
    final_state = app.invoke(initial_state, config=config)

    print("\n" + "="*50)
    print("📋 PIPELINE COMPLETE")
    print("="*50)
    print(f"Delivery Status: {final_state['delivery_status']}")
    if final_state.get("candidate_signal"):
        signal = final_state["candidate_signal"]
        print(f"Signal:          {signal.get('pair', 'N/A')} {signal.get('direction', 'N/A')}")
        print(f"Confidence:      {signal.get('confidence', 0)}/100")
    print("="*50 + "\n")

    return final_state


if __name__ == "__main__":
    run_signal_pipeline()