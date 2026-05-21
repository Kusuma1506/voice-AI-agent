import base64


class TextToSpeechService:
    async def synthesize(self, text: str, language: str) -> dict[str, str]:
        audio_bytes = f"{language}:{text}".encode("utf-8")
        return {
            "mime_type": "audio/mock;base64",
            "audio": base64.b64encode(audio_bytes).decode("ascii"),
        }

