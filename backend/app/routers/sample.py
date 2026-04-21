from fastapi import APIRouter, Depends, HTTPException, Request
import hashlib

from ..config import ROLE_ACCOUNTING, ROLE_ADMIN, ROLE_QA, ROLE_SENIOR_TECH, ROLE_LAB_TECH
from ..schemas import SampleRegistrationRequest
from ..services.audit_service import log_event
from ..services.auth_service import require_roles
from ..services.sample_service import create_sample_only, dashboard, get_sample, list_reviews, list_samples

router = APIRouter(prefix="/api", tags=["Samples"])


@router.post("/samples")
def create_sample(
    payload: SampleRegistrationRequest,
    request: Request,
    current_user=Depends(require_roles(ROLE_LAB_TECH, ROLE_SENIOR_TECH)),
):
    material_map = {
        "concrete": "Concrete",
        "rsb": "Reinforcing Steel Bar",
        "soil_aggregates": "Soil Aggregates",
        "Concrete": "Concrete",
        "Reinforcing Steel Bar": "Reinforcing Steel Bar",
        "Soil Aggregates": "Soil Aggregates",
    }

    material_type = material_map.get(payload.material_type)
    if not material_type:
        raise HTTPException(
            status_code=400,
            detail="material_type must be one of concrete, rsb, soil_aggregates.",
        )

    db_decision = "Auto-Accepted" if payload.decision == "AUTO_ACCEPTED" else "Manual-Review"
    state = "Registered" if payload.decision == "AUTO_ACCEPTED" else "For Review"
    immutable = payload.decision == "AUTO_ACCEPTED"

    ai_predicted_label = (
        material_map.get(payload.ai_predicted_label, payload.ai_predicted_label)
        if payload.ai_predicted_label
        else material_type
    )

    sample = create_sample_only(
        client_name=payload.client_name.strip(),
        project_reference=payload.project_id.strip(),
        material_type=material_type,
        current_state=state,
        branch_id=payload.branch_id,
        registered_by=current_user["user_id"],
        registered_by_role=current_user["role"],
        image_path=payload.image_path,
        is_immutable=immutable,
        ai_predicted_label=ai_predicted_label,
        confidence_score=float(payload.ai_confidence_score or 0.0),
        decision=db_decision,
        model_version=payload.model_version,
        device_metadata=payload.device_metadata or {},
        original_filename=payload.image_path.split("/")[-1] if payload.image_path else None,
        image_sha256=hashlib.sha256(payload.image_path.encode("utf-8")).hexdigest() if payload.image_path else None,
        notes=None,
    )

    sample = get_sample(sample["sample_id"])

    log_event(
        action="CREATE_SAMPLE",
        endpoint_accessed="/api/samples",
        user_id=current_user["user_id"],
        sample_id=None,
        new_value=sample,
        ip_address=request.client.host if request.client else None,
    )
    return sample


@router.get("/samples")
def samples(
    request: Request,
    current_user=Depends(
        require_roles(ROLE_LAB_TECH, ROLE_SENIOR_TECH, ROLE_QA, ROLE_ADMIN, ROLE_ACCOUNTING)
    ),
):
    data = list_samples()
    log_event(
        action="LIST_SAMPLES",
        endpoint_accessed="/api/samples",
        user_id=current_user["user_id"],
        new_value={"count": len(data)},
        ip_address=request.client.host if request.client else None,
    )
    return data


@router.get("/samples/{sample_id}")
def sample_detail(
    sample_id: str,
    request: Request,
    current_user=Depends(
        require_roles(ROLE_LAB_TECH, ROLE_SENIOR_TECH, ROLE_QA, ROLE_ADMIN, ROLE_ACCOUNTING)
    ),
):
    item = get_sample(sample_id)
    if not item:
        raise HTTPException(status_code=404, detail="Sample not found")

    log_event(
        action="VIEW_SAMPLE",
        endpoint_accessed=f"/api/samples/{sample_id}",
        user_id=current_user["user_id"],
        sample_id=None,
        new_value={"sample_id": sample_id},
        ip_address=request.client.host if request.client else None,
    )
    return item


@router.get("/reviews")
def reviews(
    request: Request,
    current_user=Depends(require_roles(ROLE_LAB_TECH, ROLE_SENIOR_TECH, ROLE_QA, ROLE_ADMIN)),
):
    data = list_reviews()
    log_event(
        action="LIST_REVIEWS",
        endpoint_accessed="/api/reviews",
        user_id=current_user["user_id"],
        new_value={"count": len(data)},
        ip_address=request.client.host if request.client else None,
    )
    return data


@router.get("/dashboard")
def technical_dashboard(
    request: Request,
    current_user=Depends(
        require_roles(ROLE_LAB_TECH, ROLE_SENIOR_TECH, ROLE_QA, ROLE_ADMIN, ROLE_ACCOUNTING)
    ),
):
    data = dashboard()
    log_event(
        action="VIEW_DASHBOARD",
        endpoint_accessed="/api/dashboard",
        user_id=current_user["user_id"],
        new_value={k: v for k, v in data.items() if k != "recent_samples"},
        ip_address=request.client.host if request.client else None,
    )
    return data