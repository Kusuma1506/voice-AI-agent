from datetime import date, timedelta

from scheduler.appointment_engine import AppointmentEngine
from scheduler.models import AppointmentRequest, CancelRequest, RescheduleRequest


def future_date() -> str:
    return (date.today() + timedelta(days=2)).isoformat()


def test_booking_conflict_returns_alternatives(tmp_path):
    engine = AppointmentEngine(path=str(tmp_path / "store.json"))
    request = AppointmentRequest(
        patient_id="pat-1",
        doctor_id="doc-cardio-1",
        date=future_date(),
        time="10:30",
    )

    first = engine.book(request)
    second = engine.book(request)

    assert first.success is True
    assert second.success is False
    assert "10:30" not in second.alternatives
    assert "14:00" in second.alternatives


def test_cancel_and_reschedule(tmp_path):
    engine = AppointmentEngine(path=str(tmp_path / "store.json"))
    booked = engine.book(
        AppointmentRequest(
            patient_id="pat-1",
            doctor_id="doc-derm-1",
            date=future_date(),
            time="09:30",
        )
    )

    moved = engine.reschedule(
        RescheduleRequest(
            patient_id="pat-1",
            appointment_id=booked.appointment_id,
            date=future_date(),
            time="14:00",
        )
    )
    cancelled = engine.cancel(CancelRequest(patient_id="pat-1", appointment_id=booked.appointment_id))

    assert moved.success is True
    assert moved.appointment["time"] == "14:00"
    assert cancelled.success is True
    assert cancelled.appointment["status"] == "cancelled"

