from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceCreateRequest(BaseModel):
    evidence_type: str = Field(min_length=1, max_length=30)
    evidence_reference: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=10, max_length=5000)
    content_hash: Optional[str] = Field(default=None, min_length=64, max_length=64)
    added_by: str = Field(min_length=1, max_length=100)

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, value):
        allowed = {
            "TEXT_MATCH",
            "CODE_MATCH",
            "DOCUMENT",
            "SCREENSHOT",
            "WITNESS_STATEMENT",
            "OTHER",
        }
        value = value.strip().upper()
        if value not in allowed:
            raise ValueError(f"evidence_type must be one of {sorted(allowed)}")
        return value

    @field_validator("content_hash")
    @classmethod
    def validate_hash(cls, value):
        if value is not None:
            value = value.strip().lower()
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("content_hash must be a 64-character SHA-256 hex digest")
        return value


class EvidenceCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    case_id: str
    evidence_type: str
    evidence_reference: str
    version: int
    added_by: str
    created_at: object
    case_status: str
