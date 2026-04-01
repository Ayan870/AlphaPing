# app/models/signal.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class CandidateSignal(BaseModel):
    pair:          Optional[str]   = None
    coin:          Optional[str]   = None
    direction:     str             = "NO_TRADE"
    entry_low:     Optional[float] = None
    entry_high:    Optional[float] = None
    stop_loss:     Optional[float] = None
    tp1:           Optional[float] = None
    tp2:           Optional[float] = None
    tp3:           Optional[float] = None
    confidence:    int             = 0
    risk_score:    int             = 5
    setup_type:    Optional[str]   = None
    timeframe:     Optional[str]   = "1h"
    raw_rationale: Optional[str]   = None


class PerformanceLog(BaseModel):
    sent_at:    Optional[str]   = None
    entry_hit:  bool            = False
    tp1_hit:    bool            = False
    tp2_hit:    bool            = False
    tp3_hit:    bool            = False
    sl_hit:     bool            = False
    final_pnl:  float           = 0.0
    result:     str             = "pending"


class SignalRecord(BaseModel):
    id:               Optional[int]   = None
    thread_id:        str
    pair:             Optional[str]   = None
    direction:        Optional[str]   = None
    entry_low:        Optional[float] = None
    entry_high:       Optional[float] = None
    stop_loss:        Optional[float] = None
    tp1:              Optional[float] = None
    tp2:              Optional[float] = None
    tp3:              Optional[float] = None
    confidence:       Optional[int]   = None
    risk_score:       Optional[int]   = None
    setup_type:       Optional[str]   = None
    timeframe:        Optional[str]   = None
    research_summary: Optional[str]   = None
    whatsapp_message: Optional[str]   = None
    human_approved:   Optional[int]   = None
    human_feedback:   Optional[str]   = None
    compliance_passed: Optional[int]  = None
    delivery_status:  Optional[str]   = None
    performance_log:  Optional[str]   = None
    created_at:       Optional[str]   = None
    updated_at:       Optional[str]   = None

    model_config = ConfigDict(from_attributes=True)