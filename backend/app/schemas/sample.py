from pydantic import BaseModel


class SampleRegistrationRequest(BaseModel):
    client_name: str
    project_id: str
    branch_id: int
    material_type: str
    image_path: str
    ai_predicted_label: str | None = None
    ai_confidence_score: float | None = None
    model_version: str | None = None
    decision: str | None = None
    device_metadata: dict | None = None


class ValidateRequest(BaseModel):
    sample_id: str
    corrected_label: str
    justification: str