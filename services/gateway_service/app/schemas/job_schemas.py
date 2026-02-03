from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateJobRequest(BaseModel):
    """Request schema that accepts camelCase from frontend."""

    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = None
    company: Optional[str] = None
    resume_text: str = Field(alias="resumeText")
    job_description: str = Field(alias="jobDescription")
    custom_instructions: Optional[str] = Field(default=None, alias="customInstructions")
    resume_lang: str = Field(pattern="^(en|ar)$", alias="resumeLang")
    jd_lang: str = Field(pattern="^(en|ar)$", alias="jdLang")
    desired_output_lang: Optional[str] = Field(
        default=None, pattern="^(en|ar)$", alias="desiredOutputLang"
    )
