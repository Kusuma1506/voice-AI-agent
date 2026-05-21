from __future__ import annotations

import re
from datetime import date, timedelta

from agent.models import AgentDecision
from memory.memory_store import MemoryStore
from services.language_detection.detector import LanguageDetector


class ClinicalAgent:
    """Small deterministic agent with the same JSON contract an LLM tool caller would use."""

    def __init__(self, memory: MemoryStore | None = None) -> None:
        self.memory = memory or MemoryStore()
        self.detector = LanguageDetector()

    def decide(self, session_id: str, patient_id: str, text: str) -> AgentDecision:
        language = self.detector.detect(text)
        normalized = text.strip().lower()
        session = self.memory.get_session(session_id)
        persistent = self.memory.get_patient(patient_id)

        intent = self._intent(normalized, session.get("pending_intent"))
        specialty = self._specialty(normalized) or session.get("specialty") or persistent.get("preferred_specialty")
        date_value = self._date(normalized) or session.get("date")
        time_value = self._time(normalized) or session.get("time")
        appointment_id = self._appointment_id(normalized) or session.get("appointment_id")

        missing = self._missing(intent, specialty, date_value, time_value, appointment_id)
        decision = AgentDecision(
            intent=intent,
            specialty=specialty,
            date=date_value,
            time=time_value,
            appointment_id=appointment_id,
            missing_fields=missing,
            language=language,
            response_text=self._prompt_for_missing(missing, language) if missing else "",
        )

        self.memory.update_session(
            session_id,
            {
                "pending_intent": intent if missing else None,
                "specialty": specialty,
                "date": date_value,
                "time": time_value,
                "appointment_id": appointment_id,
                "language": language,
            },
        )
        self.memory.update_patient(patient_id, {"preferred_language": language})
        return decision

    def _intent(self, text: str, pending: str | None) -> str:
        if any(word in text for word in ["cancel", "remove", "रद्द", "கான்சல்", "ரத்து"]):
            return "cancel"
        if any(word in text for word in ["reschedule", "move", "change", "postpone", "बदल", "शुक्रवार", "மாற்ற"]):
            return "reschedule"
        if any(word in text for word in ["available", "availability", "free", "slot", "उपलब्ध", "நேரம்"]):
            return "availability"
        if any(word in text for word in ["book", "appointment", "doctor", "डॉक्टर", "मिलना", "மருத்துவர்", "பார்க்க"]):
            return "book"
        return pending or "unknown"

    def _specialty(self, text: str) -> str | None:
        mapping = {
            "cardiologist": ["cardiologist", "heart", "cardio", "हृदय", "दिल", "இதயம்"],
            "dermatologist": ["dermatologist", "skin", "त्वचा", "சரும"],
            "pediatrician": ["pediatrician", "child", "children", "बच्च", "குழந்த"],
            "general_physician": ["general", "physician", "fever", "बुखार", "காய்ச்சல்"],
        }
        for specialty, tokens in mapping.items():
            if any(token in text for token in tokens):
                return specialty
        return None

    def _date(self, text: str) -> str | None:
        today = date.today()
        if "tomorrow" in text or "कल" in text or "நாளை" in text:
            return (today + timedelta(days=1)).isoformat()
        weekday_offsets = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
            "शुक्रवार": 4,
            "வெள்ளி": 4,
        }
        for word, weekday in weekday_offsets.items():
            if word in text:
                days = (weekday - today.weekday()) % 7 or 7
                return (today + timedelta(days=days)).isoformat()
        match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
        return match.group(1) if match else None

    def _time(self, text: str) -> str | None:
        match = re.search(r"\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*(am|pm)\b", text)
        if not match:
            match_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
            return f"{int(match_24.group(1)):02d}:{match_24.group(2)}" if match_24 else None
        hour = int(match.group(1))
        minute = match.group(2) or "00"
        meridiem = match.group(3)
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute}"

    def _appointment_id(self, text: str) -> str | None:
        match = re.search(r"\bapt-[a-z0-9-]+\b", text)
        return match.group(0) if match else None

    def _missing(
        self,
        intent: str,
        specialty: str | None,
        date_value: str | None,
        time_value: str | None,
        appointment_id: str | None,
    ) -> list[str]:
        if intent == "book":
            return [field for field, value in {"specialty": specialty, "date": date_value, "time": time_value}.items() if not value]
        if intent == "availability":
            return [field for field, value in {"specialty": specialty, "date": date_value}.items() if not value]
        if intent == "cancel":
            return [] if appointment_id else ["appointment_id"]
        if intent == "reschedule":
            return [field for field, value in {"appointment_id": appointment_id, "date": date_value, "time": time_value}.items() if not value]
        return ["intent"]

    def _prompt_for_missing(self, missing: list[str], language: str) -> str:
        field = missing[0]
        prompts = {
            "en": {
                "intent": "How can I help with your appointment?",
                "specialty": "Which doctor or specialty would you like?",
                "date": "Which date should I check?",
                "time": "What time works for you?",
                "appointment_id": "Please share your appointment ID.",
            },
            "hi": {
                "intent": "मैं आपकी अपॉइंटमेंट में कैसे मदद करूँ?",
                "specialty": "आप किस डॉक्टर या विशेषज्ञ से मिलना चाहते हैं?",
                "date": "किस तारीख के लिए देखना है?",
                "time": "कौन सा समय ठीक रहेगा?",
                "appointment_id": "कृपया अपना अपॉइंटमेंट आईडी बताइए।",
            },
            "ta": {
                "intent": "உங்கள் நேர்முகத்தில் எப்படி உதவலாம்?",
                "specialty": "எந்த மருத்துவர் அல்லது சிறப்பு துறை வேண்டும்?",
                "date": "எந்த தேதியை பார்க்க வேண்டும்?",
                "time": "எந்த நேரம் உங்களுக்கு சரி?",
                "appointment_id": "உங்கள் appointment ID-ஐ சொல்லுங்கள்.",
            },
        }
        return prompts.get(language, prompts["en"])[field]

