"""
Background Worker: Polls task_queue and processes optimization tasks.
"""

import asyncio

from libs.ai import get_llm_provider
from libs.common import get_settings
from libs.common.logging import get_logger
from libs.db.session import get_async_db

from .core.optimizer import ResumeOptimizer
from .db.models import JobStatusEnum, TaskTypeEnum
from .db.repo import Repository

settings = get_settings()
logger = get_logger(__name__)


async def process_task(task: dict, optimizer: ResumeOptimizer, db_session):
    task_id = task["id"]
    payload = task["payload"]
    logger.info(f"Processing task {task_id}")

    repo = Repository(db_session)

    try:
        # Run optimization pipeline (returns result + metrics)
        result, metrics = await optimizer.optimize(payload)

        # Update job with result
        job_id = payload["job_id"]
        user_id = payload["user_id"]

        # Build full report including metrics for Chapter 5 evaluation
        report_json = result.model_dump()
        report_json["reliability"] = metrics.model_dump()

        # Create optimization record
        # resume_id and resume_version_id are optional - can be None if not using resume storage
        await repo.create_optimization(
            user_id=user_id,
            resume_id=payload.get("resume_id") or None,
            resume_version_id=payload.get("resume_version_id") or None,
            job_id=job_id,
            score=result.score,
            report_json=report_json,
            preview_md=result.preview_markdown,
            change_log=result.change_log,
        )

        await repo.update_job_status(job_id, JobStatusEnum.complete)
        await db_session.commit()

        logger.info(
            f"Task {task_id} completed: score={result.score}, "
            f"latency={metrics.latency_seconds}s, "
            f"invalid_attempts={metrics.invalid_json_attempts}/{metrics.total_attempts}"
        )

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        await db_session.rollback()
        # Mark task as failed
        try:
            from .db.models import TaskQueue
            from .db.models import TaskStatusEnum as TS

            task_row = await db_session.get(TaskQueue, task_id)
            if task_row:
                task_row.status = TS.failed
                task_row.last_error = str(e)
                await db_session.commit()
        except Exception:
            pass


async def run_worker():
    logger.info("Starting Orchestrator Worker...")

    llm_provider = get_llm_provider()
    optimizer = ResumeOptimizer(llm_provider)
    logger.info(f"Using LLM Provider: {llm_provider.__class__.__name__}")

    poll_interval = int(settings.ENVIRONMENT == "development" and 2 or 5)

    while True:
        try:
            async for db_session in get_async_db():
                repo = Repository(db_session)

                # Poll for queued tasks
                # Note: This is simplified. In production, use SELECT FOR UPDATE SKIP LOCKED
                from sqlalchemy import select

                from .db.models import TaskQueue, TaskStatusEnum

                stmt = (
                    select(TaskQueue)
                    .where(TaskQueue.status == TaskStatusEnum.queued)
                    .where(TaskQueue.task_type == TaskTypeEnum.optimize)
                    .order_by(TaskQueue.created_at)
                    .limit(1)
                )
                result = await db_session.execute(stmt)
                task_row = result.scalar_one_or_none()

                if task_row:
                    task = {
                        "id": str(task_row.id),
                        "payload": task_row.payload,
                        "attempts": task_row.attempts,
                    }
                    # Mark as processing
                    task_row.status = TaskStatusEnum.processing
                    task_row.attempts += 1
                    await db_session.commit()

                    await process_task(task, optimizer, db_session)
                else:
                    await asyncio.sleep(poll_interval)

        except asyncio.CancelledError:
            logger.info("Worker shutdown requested")
            break
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            await asyncio.sleep(5)
