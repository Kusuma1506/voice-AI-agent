# API Examples

Start the server:

```bash
python -m uvicorn backend.main:app --reload
```

Book from a voice turn:

```bash
curl -X POST http://localhost:8000/voice/turn \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","patient_id":"pat-1","text":"Book appointment with cardiologist tomorrow at 10:30"}'
```

Create an outbound reminder task:

```bash
curl -X POST http://localhost:8000/campaigns/outbound \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"pat-1","campaign_type":"reminder","language":"en"}'
```

WebSocket message shape:

```json
{
  "text": "Move apt-12345678 to Friday at 2 pm",
  "audio": ""
}
```
