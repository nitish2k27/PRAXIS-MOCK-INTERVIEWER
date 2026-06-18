"""Resume + JD upload endpoints. Files land in object storage; rows created in Postgres."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from praxis.auth.deps import get_current_user
from praxis.db.models import JobDescription, Resume, User
from praxis.db.session import get_session
from praxis.storage import StorageBackend, get_storage

router = APIRouter(tags=["uploads"])

ALLOWED_RESUME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/resumes", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict[str, Any]:
    if file.content_type not in ALLOWED_RESUME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"unsupported content type: {file.content_type}",
        )
    key = f"resumes/{user.id}/{uuid.uuid4()}-{file.filename or 'resume'}"
    url = await storage.put(key=key, fileobj=file.file, content_type=file.content_type)
    resume = Resume(user_id=user.id, file_url=url)
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return {"id": resume.id, "file_url": resume.file_url}


@router.post("/job_descriptions", status_code=status.HTTP_201_CREATED)
async def upload_jd(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    raw_text: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> dict[str, Any]:
    if not raw_text and file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="provide raw_text or file",
        )
    file_url: str | None = None
    if file is not None:
        key = f"jds/{user.id}/{uuid.uuid4()}-{file.filename or 'jd'}"
        file_url = await storage.put(key=key, fileobj=file.file, content_type=file.content_type)
    jd = JobDescription(user_id=user.id, raw_text=raw_text, file_url=file_url)
    session.add(jd)
    await session.commit()
    await session.refresh(jd)
    return {"id": jd.id, "file_url": jd.file_url, "raw_text": jd.raw_text}
