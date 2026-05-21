class SpeechToTextService:
    async def transcribe(self, audio_payload: str, transcript_hint: str | None = None) -> str:
        if transcript_hint:
            return transcript_hint
        if audio_payload.startswith("text:"):
            return audio_payload.removeprefix("text:").strip()
        return audio_payload.strip()

