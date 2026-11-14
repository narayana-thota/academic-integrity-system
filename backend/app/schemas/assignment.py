
from pydantic import BaseModel, Field


class AssignmentCreateRequest(BaseModel):
    reviewer_id: int = Field(gt=0)
    assigned_by: str = Field(min_length=2, max_length=100)
