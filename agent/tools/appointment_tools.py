from scheduler.appointment_engine import AppointmentEngine
from scheduler.models import AppointmentRequest, CancelRequest, RescheduleRequest


class AppointmentTools:
    def __init__(self, engine: AppointmentEngine | None = None) -> None:
        self.engine = engine or AppointmentEngine()

    def check_availability(self, specialty: str, date: str):
        doctor = self.engine.find_doctor_by_specialty(specialty)
        if not doctor:
            return {"success": False, "message": "No doctor found for that specialty.", "alternatives": []}
        return self.engine.check_availability(doctor_id=doctor["id"], date=date)

    def book(self, patient_id: str, specialty: str, date: str, time: str):
        doctor = self.engine.find_doctor_by_specialty(specialty)
        if not doctor:
            return {"success": False, "message": "No doctor found for that specialty.", "alternatives": []}
        request = AppointmentRequest(patient_id=patient_id, doctor_id=doctor["id"], date=date, time=time)
        return self.engine.book(request).model_dump()

    def cancel(self, appointment_id: str, patient_id: str):
        return self.engine.cancel(CancelRequest(appointment_id=appointment_id, patient_id=patient_id)).model_dump()

    def reschedule(self, appointment_id: str, patient_id: str, date: str, time: str):
        request = RescheduleRequest(appointment_id=appointment_id, patient_id=patient_id, date=date, time=time)
        return self.engine.reschedule(request).model_dump()

