from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CreateJobRequest(BaseModel):
    user_id: str
    title: Optional[str] = None
    company: Optional[str] = None
    resume_text: str
    job_description: str
    custom_instructions: Optional[str] = None
    resume_lang: str = Field(pattern="^(en|ar)$")
    jd_lang: str = Field(pattern="^(en|ar)$")
    desired_output_lang: Optional[str] = Field(default=None, pattern="^(en|ar)$")


class RefineJobRequest(BaseModel):
    """Request schema for job refinement."""

    user_id: str
    instructions: str
    desired_output_lang: Optional[str] = Field(default=None, pattern="^(en|ar)$")


class JobResponse(BaseModel):
    """Response schema with camelCase field names for frontend compatibility."""

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: Any  # UUID gets converted to string
    user_id: Any
    title: str
    company: Optional[str]
    status: str
    resume_lang: str
    jd_lang: str
    desired_output_lang: str
    created_at: Any  # datetime gets converted to ISO string
    updated_at: Any

    @field_serializer("id", "user_id")
    def serialize_uuid(self, v):
        return str(v) if v else None

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else None


class OptimizationResultResponse(BaseModel):
    """Response schema for optimization results with camelCase."""

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    score: int
    missing_keywords: list[str] = Field(default_factory=list)
    covered_keywords: list[str] = Field(default_factory=list)
    change_log: list[str] = Field(default_factory=list)
    preview_markdown: str = ""
    extracted_entities: Optional[dict] = None
    alignment_insights: Optional[dict] = None
    reliability: Optional[dict] = None


class JobWithResultResponse(BaseModel):
    """Job response that includes the optimization result."""

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    user_id: str
    title: str
    company: Optional[str]
    status: str
    resume_lang: str
    jd_lang: str
    desired_output_lang: str
    created_at: str
    updated_at: str
    result: Optional[OptimizationResultResponse] = None
