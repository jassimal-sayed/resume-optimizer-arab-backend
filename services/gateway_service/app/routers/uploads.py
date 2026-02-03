"""
Uploads Router: Handles file uploads and proxies to Parser Service.
"""

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from libs.auth import get_current_user_id
from libs.common import get_settings

settings = get_settings()
router = APIRouter()

PARSER_URL = settings.PARSER_SERVICE_URL


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...), user_id: str = Depends(get_current_user_id)
):
    """
    Upload a resume file (PDF/DOCX/Image).
    Proxies to Parser Service for text extraction.
    Returns extracted text for use in job creation.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    try:
        contents = await file.read()

        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (file.filename, contents, file.content_type)}
            response = await client.post(f"{PARSER_URL}/internal/extract", files=files)
            response.raise_for_status()

            result = response.json()
            return {
                "data": {
                    "filename": result.get("filename"),
                    "text": result.get("text"),
                    "char_count": result.get("char_count"),
                    "method": result.get("method"),
                },
                "error": None,
            }

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Parser service unavailable: {e}")
