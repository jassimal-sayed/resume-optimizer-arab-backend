"""
Jobs Router: Proxies job requests to Orchestrator service.
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from libs.auth import get_current_user_id
from libs.common import envelope_error, get_settings
from pydantic import BaseModel, Field

settings = get_settings()
router = APIRouter()

# Orchestrator service URL (internal network)
ORCHESTRATOR_URL = settings.ORCHESTRATOR_SERVICE_URL


from ..schemas.job_schemas import CreateJobRequest


async def proxy_to_orchestrator(
    method: str, path: str, user_id: str, json_body: dict = None
) -> dict:
    """Helper to forward requests to Orchestrator."""
    url = f"{ORCHESTRATOR_URL}/internal{path}"

    params = {"user_id": user_id}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                # Include user_id in body for POST
                if json_body:
                    json_body["user_id"] = user_id
                else:
                    json_body = {"user_id": user_id}
                print(f"DEBUG: Proxying POST to {url}")
                response = await client.post(url, json=json_body)
            else:
                raise ValueError(f"Unsupported method: {method}")

            print(f"DEBUG: Response Status: {response.status_code}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            # Forward error from Orchestrator
            try:
                detail = e.response.json()
            except:
                detail = envelope_error(str(e))
            raise HTTPException(status_code=e.response.status_code, detail=detail)
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=envelope_error(f"Orchestrator unavailable: {e}")
            )


@router.post("", response_model=dict)
async def create_job(
    payload: CreateJobRequest, user_id: str = Depends(get_current_user_id)
):
    return await proxy_to_orchestrator("POST", "/jobs", user_id, payload.model_dump())


@router.get("", response_model=dict)
async def list_jobs(user_id: str = Depends(get_current_user_id)):
    return await proxy_to_orchestrator("GET", "/jobs", user_id)


@router.get("/{job_id}", response_model=dict)
async def get_job(job_id: str, user_id: str = Depends(get_current_user_id)):
    return await proxy_to_orchestrator("GET", f"/jobs/{job_id}", user_id)


class RefineJobRequest(BaseModel):
    """Request schema for job refinement from frontend."""

    instructions: str
    desired_output_lang: Optional[str] = Field(default=None, pattern="^(en|ar)$")


@router.post("/{job_id}/refine", response_model=dict)
async def refine_job(
    job_id: str, payload: RefineJobRequest, user_id: str = Depends(get_current_user_id)
):
    """Refine an existing job with new instructions."""
    return await proxy_to_orchestrator(
        "POST", f"/jobs/{job_id}/refine", user_id, payload.model_dump()
    )
