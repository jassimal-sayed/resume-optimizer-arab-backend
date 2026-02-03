from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Job,
    JobStatusEnum,
    Optimization,
    Resume,
    ResumeVersion,
    TaskQueue,
    TaskTypeEnum,
)


class Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_resume(
        self,
        user_id: str,
        title: str,
        source: str,
        file_url: Optional[str] = None,
        raw_text: Optional[str] = None,
        parsed_json: Optional[dict] = None,
    ) -> str:
        resume = Resume(user_id=user_id, title=title, file_url=file_url, source=source)
        self.session.add(resume)
        await self.session.flush()
        version = ResumeVersion(
            resume_id=resume.id, raw_text=raw_text, parsed_json=parsed_json
        )
        self.session.add(version)
        await self.session.flush()
        resume.active_version_id = version.id
        await self.session.flush()
        return str(resume.id)

    async def create_job(self, user_id: str, payload: Dict[str, Any]) -> Job:
        job = Job(
            user_id=user_id,
            title=payload["title"],
            company=payload.get("company"),
            job_description=payload["job_description"],
            parsed_json=payload.get("parsed_json"),
            custom_instructions=payload.get("custom_instructions"),
            resume_lang=payload["resume_lang"],
            jd_lang=payload["jd_lang"],
            desired_output_lang=payload.get("desired_output_lang")
            or payload["resume_lang"],
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job_for_user(self, user_id: str, job_id: str) -> Optional[Job]:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id, Job.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_jobs_for_user(self, user_id: str) -> List[Job]:
        result = await self.session.execute(
            select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_jobs_for_user_paginated(
        self, user_id: str, limit: int, offset: int
    ) -> List[Job]:
        stmt = (
            select(Job)
            .where(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def enqueue_task(
        self, task_type: TaskTypeEnum, payload: Dict[str, Any]
    ) -> str:
        task = TaskQueue(task_type=task_type, payload=payload)
        self.session.add(task)
        await self.session.flush()
        return str(task.id)

    async def update_job_status(self, job_id: str, status: JobStatusEnum) -> None:
        await self.session.execute(
            update(Job).where(Job.id == job_id).values(status=status)
        )

    async def update_job_with_callback(
        self, job_id: str, user_id: str, raw_text: str, parsed_json: Optional[dict]
    ) -> Optional[Job]:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id, Job.user_id == user_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return None
        job.job_description = raw_text
        job.parsed_json = parsed_json
        await self.session.flush()
        return job

    async def update_resume_version_callback(
        self, resume_id: str, user_id: str, raw_text: str, parsed_json: Optional[dict]
    ) -> Optional[ResumeVersion]:
        res = await self.session.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = res.scalar_one_or_none()
        if not resume:
            return None
        ver_res = await self.session.execute(
            select(ResumeVersion).where(
                ResumeVersion.id == resume.active_version_id,
                ResumeVersion.resume_id == resume_id,
            )
        )
        version = ver_res.scalar_one_or_none()
        if not version:
            return None
        version.raw_text = raw_text
        version.parsed_json = parsed_json
        await self.session.flush()
        return version

    async def create_optimization(
        self,
        user_id: str,
        resume_id: str,
        resume_version_id: str,
        job_id: str,
        score: int,
        report_json: dict,
        preview_md: str,
        change_log: Optional[list],
    ) -> Optimization:
        opt = Optimization(
            user_id=user_id,
            resume_id=resume_id,
            resume_version_id=resume_version_id,
            job_id=job_id,
            score=score,
            report_json=report_json,
            preview_md=preview_md,
            change_log=change_log,
        )
        self.session.add(opt)
        await self.session.flush()
        return opt

    async def get_latest_optimization_for_job(
        self, job_id: str, user_id: str
    ) -> Optional[Optimization]:
        stmt = (
            select(Optimization)
            .where(Optimization.job_id == job_id, Optimization.user_id == user_id)
            .order_by(desc(Optimization.created_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_task_for_job(self, job_id: str) -> Optional[TaskQueue]:
        """Get the original task for a job to retrieve resume_text for refinement."""
        # Find task where payload contains this job_id
        # Note: This assumes payload is JSONB and we can filter on it
        stmt = (
            select(TaskQueue)
            .where(TaskQueue.payload["job_id"].astext == job_id)
            .order_by(TaskQueue.created_at)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
