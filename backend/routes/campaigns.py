from fastapi import APIRouter
from pydantic import BaseModel

from scheduler.campaigns import CampaignScheduler

router = APIRouter()
scheduler = CampaignScheduler()


class CampaignRequest(BaseModel):
    patient_id: str
    campaign_type: str
    language: str = "en"
    appointment_id: str | None = None


@router.post("/outbound")
def create_outbound_call(request: CampaignRequest):
    return scheduler.create_call_task(request.model_dump())


@router.get("/outbound")
def list_outbound_calls():
    return {"tasks": scheduler.list_tasks()}

