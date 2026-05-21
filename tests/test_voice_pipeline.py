from datetime import date, timedelta
import asyncio

from services.voice_pipeline import VoicePipeline


def test_voice_turn_books_and_logs_latency(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AI_DATA_PATH", str(tmp_path / "store.json"))
    monkeypatch.setenv("VOICE_AI_LOG_PATH", str(tmp_path / "latency.jsonl"))
    pipeline = VoicePipeline()
    target_date = (date.today() + timedelta(days=2)).isoformat()

    result = asyncio.run(
        pipeline.handle_turn(
            session_id="sess-1",
            patient_id="pat-1",
            audio_payload="",
            transcript_hint=f"Book appointment with cardiologist on {target_date} at 10:30",
        )
    )

    assert result.language == "en"
    assert "Appointment confirmed" in result.text_response
    assert result.tool_result["success"] is True
    assert "total_ms" in result.latency
    assert (tmp_path / "latency.jsonl").exists()


def test_voice_turn_detects_hindi_and_asks_missing_time(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_AI_DATA_PATH", str(tmp_path / "store.json"))
    monkeypatch.setenv("VOICE_AI_LOG_PATH", str(tmp_path / "latency.jsonl"))
    pipeline = VoicePipeline()

    result = asyncio.run(
        pipeline.handle_turn(
            session_id="sess-hi",
            patient_id="pat-hi",
            audio_payload="",
            transcript_hint="मुझे कल दिल के डॉक्टर से मिलना है",
        )
    )

    assert result.language == "hi"
    assert result.tool_result is None
    assert "समय" in result.text_response
