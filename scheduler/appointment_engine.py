from __future__ import annotations

import json
import os
from datetime import date as date_type
from datetime import datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4

from scheduler.models import AppointmentRequest, AppointmentResult, CancelRequest, RescheduleRequest

DEFAULT_DOCTORS = [
    {"id": "doc-cardio-1", "name": "Dr Sharma", "specialty": "cardiologist"},
    {"id": "doc-derm-1", "name": "Dr Meenakshi", "specialty": "dermatologist"},
    {"id": "doc-peds-1", "name": "Dr Iyer", "specialty": "pediatrician"},
    {"id": "doc-gp-1", "name": "Dr Khan", "specialty": "general_physician"},
]

DEFAULT_SLOTS = ["09:30", "10:30", "14:00", "16:30"]


class AppointmentEngine:
    _lock = Lock()

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("VOICE_AI_DATA_PATH", "./data/store.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"sessions": {}, "patients": {}, "appointments": {}, "campaigns": []})

    def list_doctors(self) -> list[dict]:
        return DEFAULT_DOCTORS

    def find_doctor_by_specialty(self, specialty: str) -> dict | None:
        return next((doctor for doctor in DEFAULT_DOCTORS if doctor["specialty"] == specialty), None)

    def check_availability(self, doctor_id: str, date: str) -> dict:
        if not self._valid_doctor(doctor_id):
            return {"success": False, "message": "Invalid doctor ID.", "available_slots": []}
        booked = {
            appointment["time"]
            for appointment in self._read()["appointments"].values()
            if appointment["doctor_id"] == doctor_id
            and appointment["date"] == date
            and appointment["status"] == "booked"
        }
        return {
            "success": True,
            "doctor_id": doctor_id,
            "date": date,
            "available_slots": [slot for slot in DEFAULT_SLOTS if slot not in booked],
        }

    def book(self, request: AppointmentRequest) -> AppointmentResult:
        validation = self._validate_slot(request.doctor_id, request.date, request.time)
        if validation:
            return validation

        data = self._read()
        appointment_id = f"apt-{uuid4().hex[:8]}"
        appointment = {
            "id": appointment_id,
            "patient_id": request.patient_id,
            "doctor_id": request.doctor_id,
            "date": request.date,
            "time": request.time,
            "status": "booked",
        }
        data["appointments"][appointment_id] = appointment
        patient = data["patients"].setdefault(request.patient_id, {"past_appointments": []})
        patient.setdefault("past_appointments", []).append(appointment_id)
        self._write(data)
        return AppointmentResult(
            success=True,
            message="Appointment confirmed.",
            appointment_id=appointment_id,
            appointment=appointment,
        )

    def cancel(self, request: CancelRequest) -> AppointmentResult:
        data = self._read()
        appointment = data["appointments"].get(request.appointment_id)
        if not appointment or appointment["patient_id"] != request.patient_id:
            return AppointmentResult(success=False, message="Appointment not found.")
        appointment["status"] = "cancelled"
        self._write(data)
        return AppointmentResult(
            success=True,
            message="Appointment cancelled.",
            appointment_id=request.appointment_id,
            appointment=appointment,
        )

    def reschedule(self, request: RescheduleRequest) -> AppointmentResult:
        data = self._read()
        appointment = data["appointments"].get(request.appointment_id)
        if not appointment or appointment["patient_id"] != request.patient_id:
            return AppointmentResult(success=False, message="Appointment not found.")
        validation = self._validate_slot(appointment["doctor_id"], request.date, request.time, ignore_id=request.appointment_id)
        if validation:
            return validation
        appointment["date"] = request.date
        appointment["time"] = request.time
        appointment["status"] = "booked"
        self._write(data)
        return AppointmentResult(
            success=True,
            message="Appointment rescheduled.",
            appointment_id=request.appointment_id,
            appointment=appointment,
        )

    def _validate_slot(
        self,
        doctor_id: str,
        date: str,
        time: str,
        ignore_id: str | None = None,
    ) -> AppointmentResult | None:
        if not self._valid_doctor(doctor_id):
            return AppointmentResult(success=False, message="Invalid doctor ID.")
        if time not in DEFAULT_SLOTS:
            return AppointmentResult(
                success=False,
                message="Requested slot is unavailable.",
                alternatives=self.check_availability(doctor_id, date)["available_slots"],
            )
        requested = datetime.fromisoformat(f"{date}T{time}:00")
        if requested < datetime.now():
            return AppointmentResult(success=False, message="Cannot book an appointment in the past.")
        data = self._read()
        for appointment_id, appointment in data["appointments"].items():
            if appointment_id == ignore_id:
                continue
            if (
                appointment["doctor_id"] == doctor_id
                and appointment["date"] == date
                and appointment["time"] == time
                and appointment["status"] == "booked"
            ):
                return AppointmentResult(
                    success=False,
                    message="That slot is already booked.",
                    alternatives=self.check_availability(doctor_id, date)["available_slots"],
                )
        return None

    def _valid_doctor(self, doctor_id: str) -> bool:
        return any(doctor["id"] == doctor_id for doctor in DEFAULT_DOCTORS)

    def _read(self) -> dict:
        with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        with self._lock:
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def next_demo_date() -> str:
    return date_type.today().replace(day=min(date_type.today().day + 1, 28)).isoformat()

