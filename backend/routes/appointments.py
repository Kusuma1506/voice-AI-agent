from fastapi import APIRouter, HTTPException

from scheduler.appointment_engine import AppointmentEngine
from scheduler.models import AppointmentRequest, CancelRequest, RescheduleRequest

router = APIRouter()
engine = AppointmentEngine()


@router.get("/doctors")
def doctors():
    return {"doctors": engine.list_doctors()}


@router.get("/availability")
def availability(doctor_id: str, date: str):
    return engine.check_availability(doctor_id=doctor_id, date=date)


@router.post("/book")
def book(request: AppointmentRequest):
    result = engine.book(request)
    if not result.success:
        raise HTTPException(status_code=409, detail=result.model_dump())
    return result


@router.post("/cancel")
def cancel(request: CancelRequest):
    result = engine.cancel(request)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.model_dump())
    return result


@router.post("/reschedule")
def reschedule(request: RescheduleRequest):
    result = engine.reschedule(request)
    if not result.success:
        raise HTTPException(status_code=409, detail=result.model_dump())
    return result

