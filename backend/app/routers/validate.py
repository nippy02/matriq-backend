from fastapi import APIRouter, Depends, HTTPException, Request

from ..config import LABEL_TO_DB, ROLE_SENIOR_TECH
from ..schemas import ValidateRequest
from ..services.audit_service import log_event
from ..services.auth_service import require_roles
from ..services.sample_service import complete_review, get_review_by_sample_id

router = APIRouter(prefix='/api', tags=['Validation'])


@router.post('/validate')
def validate(payload: ValidateRequest, request: Request, current_user=Depends(require_roles(ROLE_SENIOR_TECH))):
    if payload.final_label not in LABEL_TO_DB:
        raise HTTPException(status_code=400, detail='final_label must be one of concrete, rsb, soil_aggregates.')
    if not payload.review_case_id.startswith('SAMPLE-'):
        raise HTTPException(status_code=400, detail='review_case_id must use SAMPLE-<id> format.')
    sample_id = int(payload.review_case_id.split('-', 1)[1])
    review = get_review_by_sample_id(sample_id)
    if not review:
        raise HTTPException(status_code=404, detail='Review case not found.')
    if review['status'] == 'Completed':
        raise HTTPException(status_code=400, detail='Review case is already completed.')

    sample = complete_review(
        sample_id=sample_id,
        corrected_label_db=LABEL_TO_DB[payload.final_label],
        justification=payload.justification.strip(),
        reviewed_by=current_user['user_id'],
    )

    log_event(
        action='MANUAL_VALIDATION_SUBMITTED',
        endpoint_accessed='/api/validate',
        user_id=current_user['user_id'],
        sample_id=sample_id,
        new_value={
            'final_label': LABEL_TO_DB[payload.final_label],
            'justification': payload.justification.strip(),
            'review_case_id': payload.review_case_id,
        },
        ip_address=request.client.host if request.client else None,
    )

    return {
        'success': True,
        'message': 'Manual override completed and sample updated.',
        'review_case_id': payload.review_case_id,
        'final_label': payload.final_label,
        'sample_registration': sample,
    }
