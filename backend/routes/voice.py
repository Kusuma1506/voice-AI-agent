from fastapi import APIRouter
from pydantic import BaseModel

from services.voice_pipeline import VoicePipeline

router = APIRouter()
pipeline = VoicePipeline()


class VoiceTurnRequest(BaseModel):
    session_id: str
    patient_id: str
    audio: str = ""
    text: str | None = None


@router.post("/turn")
async def voice_turn(request: VoiceTurnRequest):
    return await pipeline.handle_turn(
        session_id=request.session_id,
        patient_id=request.patient_id,
        audio_payload=request.audio,
        transcript_hint=request.text,
    )

