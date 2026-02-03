import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from libs.common import envelope_error
from libs.db.session import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import JobStatusEnum, TaskTypeEnum
from ..db.repo import Repository
from ..schemas.job_schemas import (
    CreateJobRequest,
    JobResponse,
    OptimizationResultResponse,
    RefineJobRequest,
)

router = APIRouter(tags=["orchestrator"])


def serialize_job(job) -> dict:
    """Serialize job model to camelCase dict."""
    return JobResponse.model_validate(job).model_dump(by_alias=True)


def serialize_optimization_result(opt) -> dict:
    """Serialize optimization result to frontend-compatible format."""
    report = opt.report_json or {}
    return {
        "id": str(opt.id),
        "score": opt.score,
        "missingKeywords": report.get("missing_keywords", []),
        "coveredKeywords": report.get("covered_keywords", []),
        "changeLog": opt.change_log or [],
        "previewMarkdown": opt.preview_md or "",
        "extractedEntities": report.get("extracted_entities"),
        "alignmentInsights": report.get("alignment_insights"),
        "reliability": report.get("reliability"),
    }


@router.post("/jobs", response_model=dict)
async def create_job(
    payload: CreateJobRequest, db: AsyncSession = Depends(get_async_db)
):
    repo = Repository(db)

    job_data = {
        "title": payload.title or "Resume Optimization",
        "company": payload.company,
        "job_description": payload.job_description,
        "custom_instructions": payload.custom_instructions,
        "resume_lang": payload.resume_lang,
        "jd_lang": payload.jd_lang,
        "desired_output_lang": payload.desired_output_lang or payload.resume_lang,
    }

    job = await repo.create_job(payload.user_id, job_data)

    # Enqueue optimization task
    task_payload = {
        "job_id": str(job.id),
        "user_id": payload.user_id,
        "resume_text": payload.resume_text,
        "job_description": payload.job_description,
        "instructions": payload.custom_instructions,
        "resume_lang": payload.resume_lang,
        "jd_lang": payload.jd_lang,
        "desired_output_lang": payload.desired_output_lang or payload.resume_lang,
        "is_refinement": False,
    }
    await repo.enqueue_task(TaskTypeEnum.optimize, task_payload)
    await db.commit()

    return {"data": {"job": serialize_job(job)}, "error": None}


@router.get("/jobs", response_model=dict)
async def list_jobs(user_id: str, db: AsyncSession = Depends(get_async_db)):
    repo = Repository(db)
    jobs = await repo.list_jobs_for_user(user_id)
    return {"data": {"jobs": [serialize_job(j) for j in jobs]}, "error": None}


@router.get("/jobs/{job_id}", response_model=dict)
async def get_job(job_id: str, user_id: str, db: AsyncSession = Depends(get_async_db)):
    repo = Repository(db)
    job = await repo.get_job_for_user(user_id, job_id)

    if not job:
        raise HTTPException(status_code=404, detail=envelope_error("Job not found"))

    # Fetch optimization result if complete
    result = None
    if job.status == "complete":
        opt = await repo.get_latest_optimization_for_job(job_id, user_id)
        if opt:
            result = serialize_optimization_result(opt)

    job_dict = serialize_job(job)
    job_dict["result"] = result

    return {"data": {"job": job_dict}, "error": None}


@router.post("/jobs/{job_id}/refine", response_model=dict)
async def refine_job(
    job_id: str, payload: RefineJobRequest, db: AsyncSession = Depends(get_async_db)
):
    """
    Refine an existing completed job with new instructions.
    Creates a new optimization task and resets job status to queued.
    """
    repo = Repository(db)

    # Get existing job
    job = await repo.get_job_for_user(payload.user_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=envelope_error("Job not found"))

    if job.status != "complete":
        raise HTTPException(
            status_code=400, detail=envelope_error("Can only refine completed jobs")
        )

    # Get the original task to retrieve resume_text
    # The resume_text was stored in the task payload
    original_task = await repo.get_task_for_job(job_id)
    original_payload = original_task.payload if original_task else {}
    resume_text = original_payload.get("resume_text", "")

    # Update job status back to queued
    await repo.update_job_status(job_id, JobStatusEnum.queued)

    # Enqueue refinement task
    task_payload = {
        "job_id": str(job.id),
        "user_id": payload.user_id,
        "resume_text": resume_text,
        "job_description": job.job_description,
        "instructions": payload.instructions,
        "is_refinement": True,
        "desired_output_lang": payload.desired_output_lang or job.desired_output_lang,
        "resume_lang": job.resume_lang,
        "jd_lang": job.jd_lang,
    }
    await repo.enqueue_task(TaskTypeEnum.optimize, task_payload)
    await db.commit()

    # Refresh job to get updated status
    job = await repo.get_job_for_user(payload.user_id, job_id)

    return {"data": {"job": serialize_job(job)}, "error": None}
