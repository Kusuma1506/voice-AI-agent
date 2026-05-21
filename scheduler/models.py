from pydantic import BaseModel, Field


class AppointmentRequest(BaseModel):
    patient_id: str
    doctor_id: str
    date: str
    time: str


class CancelRequest(BaseModel):
    appointment_id: str
    patient_id: str


class RescheduleRequest(BaseModel):
    appointment_id: str
    patient_id: str
    date: str
    time: str


class AppointmentResult(BaseModel):
    success: bool
    message: str
    appointment_id: str | None = None
    alternatives: list[str] = Field(default_factory=list)
    appointment: dict | None = None

