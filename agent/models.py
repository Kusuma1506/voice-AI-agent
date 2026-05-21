from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["book", "cancel", "reschedule", "availability", "unknown"]


class AgentDecision(BaseModel):
    intent: Intent
    specialty: str | None = None
    doctor_id: str | None = None
    date: str | None = None
    time: str | None = None
    appointment_id: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    response_text: str
    language: str = "en"

