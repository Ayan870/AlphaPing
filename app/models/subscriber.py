# app/models/subscriber.py
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
import re


class Subscriber(BaseModel):
    id:         Optional[int] = None
    phone:      str
    plan:       str           = "free"
    active:     int           = 1
    joined_at:  Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        # Remove spaces and dashes
        cleaned = re.sub(r"[\s\-]", "", v)
        # Must start with + or digits
        if not re.match(r"^\+?\d{10,15}$", cleaned):
            raise ValueError(
                "Invalid phone number. "
                "Must be 10-15 digits with optional + prefix."
            )
        return cleaned

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v):
        allowed = ["free", "pro", "vip"]
        if v.lower() not in allowed:
            raise ValueError(f"Plan must be one of: {allowed}")
        return v.lower()

    model_config = ConfigDict(from_attributes=True)


class SubscriberList(BaseModel):
    total:       int
    subscribers: list[Subscriber]