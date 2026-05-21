from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.appointments import router as appointment_router
from backend.routes.campaigns import router as campaign_router
from backend.routes.voice import router as voice_router
from services.voice_pipeline import VoicePipeline

app = FastAPI(title="Clinical Voice AI Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointment_router, prefix="/appointments", tags=["appointments"])
app.include_router(campaign_router, prefix="/campaigns", tags=["campaigns"])
app.include_router(voice_router, prefix="/voice", tags=["voice"])

pipeline = VoicePipeline()


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "running"}


@app.websocket("/ws/voice/{session_id}/{patient_id}")
async def voice_socket(websocket: WebSocket, session_id: str, patient_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            result = await pipeline.handle_turn(
                session_id=session_id,
                patient_id=patient_id,
                audio_payload=payload.get("audio", ""),
                transcript_hint=payload.get("text"),
            )
            await websocket.send_json(result.model_dump())
    except WebSocketDisconnect:
        return

