"""Domain analysis routes."""

from fastapi import APIRouter, Depends

from api.dependencies import get_compliance_service
from api.schemas import ComplianceRequest
from services.compliance_service import ComplianceService

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("/compliance")
def analyze_compliance(
    request: ComplianceRequest,
    service: ComplianceService = Depends(get_compliance_service),
):
    return service.analyze(
        question=request.question,
        project=request.project,
        lot=request.lot,
        k=request.top_k,
    )
