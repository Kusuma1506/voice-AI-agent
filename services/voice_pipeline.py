from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from agent.reasoning.clinical_agent import ClinicalAgent
from agent.tools.appointment_tools import AppointmentTools
from services.latency import LatencyLogger, LatencyTracker
from services.speech_to_text import SpeechToTextService
from services.text_to_speech import TextToSpeechService


class VoiceTurnResult(BaseModel):
    transcript: str
    language: str
    text_response: str
    audio: dict[str, str]
    tool_result: dict | None
    latency: dict


class VoicePipeline:
    def __init__(self) -> None:
        self.stt = SpeechToTextService()
        self.agent = ClinicalAgent()
        self.tools = AppointmentTools()
        self.tts = TextToSpeechService()
        self.latency_logger = LatencyLogger()

    async def handle_turn(
        self,
        session_id: str,
        patient_id: str,
        audio_payload: str,
        transcript_hint: str | None = None,
    ) -> VoiceTurnResult:
        tracker = LatencyTracker()
        transcript = await self.stt.transcribe(audio_payload, transcript_hint)
        tracker.mark("stt")

        decision = self.agent.decide(session_id=session_id, patient_id=patient_id, text=transcript)
        tracker.mark("agent")

        tool_result = self._run_tool(patient_id, decision)
        response = decision.response_text or self._format_tool_response(tool_result, decision.language)
        tracker.mark("tools")

        audio = await self.tts.synthesize(response, decision.language)
        tracker.mark("tts")

        latency = tracker.report()
        self.latency_logger.log(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "session_id": session_id,
                "patient_id": patient_id,
                "intent": decision.intent,
                "latency": latency,
            }
        )
        return VoiceTurnResult(
            transcript=transcript,
            language=decision.language,
            text_response=response,
            audio=audio,
            tool_result=tool_result,
            latency=latency,
        )

    def _run_tool(self, patient_id: str, decision) -> dict | None:
        if decision.missing_fields:
            return None
        if decision.intent == "availability":
            return self.tools.check_availability(decision.specialty, decision.date)
        if decision.intent == "book":
            return self.tools.book(patient_id, decision.specialty, decision.date, decision.time)
        if decision.intent == "cancel":
            return self.tools.cancel(decision.appointment_id, patient_id)
        if decision.intent == "reschedule":
            return self.tools.reschedule(decision.appointment_id, patient_id, decision.date, decision.time)
        return None

    def _format_tool_response(self, result: dict | None, language: str) -> str:
        if not result:
            return {
                "en": "I could not understand that request. Could you repeat it?",
                "hi": "मैं अनुरोध समझ नहीं पाया। कृपया दोबारा बताइए।",
                "ta": "உங்கள் கோரிக்கையை புரிந்து கொள்ளவில்லை. மீண்டும் சொல்லுங்கள்.",
            }.get(language, "I could not understand that request. Could you repeat it?")

        if "available_slots" in result:
            slots = ", ".join(result["available_slots"]) or "none"
            return self._translate(language, f"Available slots are {slots}.")

        if result.get("success"):
            appointment_id = result.get("appointment_id")
            appointment = result.get("appointment") or {}
            details = f" {appointment.get('date', '')} at {appointment.get('time', '')}".strip()
            suffix = f" Your appointment ID is {appointment_id}." if appointment_id else ""
            return self._translate(language, f"{result['message']} {details}.{suffix}")

        alternatives = ", ".join(result.get("alternatives", []))
        alt_text = f" Available alternatives are {alternatives}." if alternatives else ""
        return self._translate(language, f"{result.get('message', 'The request failed.')}{alt_text}")

    def _translate(self, language: str, english_text: str) -> str:
        if language == "hi":
            return f"{english_text} क्या यह ठीक है?"
        if language == "ta":
            return f"{english_text} இது சரியா?"
        return english_text

