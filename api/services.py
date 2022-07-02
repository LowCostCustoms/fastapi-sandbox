from datetime import datetime
from typing import List
from uuid import UUID

from crontab import CronTab
from fastapi import Depends
import sqlalchemy as sa
import sqlalchemy.orm as sao

from api.db import get_current_session
from api.db import transactional
from api.dto import AssignJobRunDto
from api.dto import CompleteJobRunDto
from api.dto import JobDto
from api.dto import JobQueryParamsDto
from api.dto import JobRequestDto
from api.dto import JobRunDto
from api.dto import JobRunQueryParamsDto
from api.dto import JobSortField
from api.dto import Page
from api.errors import InvalidCronExpressionError
from api.errors import NotFoundError
from api.errors import RunAssignmentFailed
from api.errors import RunCompletionFailed
from api.models import Job
from api.models import JobRun
from api.models import JobRunStatus
from api.models import JobSchedule


class JobRunService:
    async def list_runs(self, params: JobRunQueryParamsDto) -> Page[JobRunDto]:
        query = sa.select(JobRun)

        if params.assignable_only:
            query = query.where(
                sa.or_(
                    JobRun.assigned_to == None,
                    JobRun.assigned_until == None,
                    JobRun.assigned_until < sa.func.now(),
                ),
                JobRun.status.in_([JobRunStatus.SCHEDULED, JobRunStatus.IN_PROGRESS]),
            )

        if params.sort is not None:
            query = query.order_by(params.sort_order.apply(params.sort.column))

        items, count = await get_current_session().get_page(query, offset=params.offset, limit=params.limit)
        return Page(count=count, results=[JobRunDto.from_orm(r) for r in items])

    async def get_run(self, id: UUID) -> JobRunDto:
        run = await get_current_session().get(JobRun, id)
        if run is None:
            raise NotFoundError(f"Could not find job run {id}.")

        return JobRunDto.from_orm(run)

    @transactional
    async def assign_run(self, id: UUID, request: AssignJobRunDto) -> JobRunDto:
        query = (
            sa.update(
                JobRun,
            )
            .values(
                assigned_to=request.worker,
                assigned_until=sa.func.now() + sa.literal(request.lease_duration, sa.Interval()),
                status=JobRunStatus.IN_PROGRESS,
            )
            .where(
                sa.and_(
                    JobRun.id == id,
                    sa.or_(
                        JobRun.assigned_to == None,
                        JobRun.assigned_to == request.worker,
                        JobRun.assigned_until == None,
                        JobRun.assigned_until < sa.func.now(),
                    ),
                    sa.or_(
                        JobRun.scheduled_at == None,
                        JobRun.scheduled_at <= sa.func.now(),
                    ),
                    JobRun.status.in_([JobRunStatus.SCHEDULED, JobRunStatus.IN_PROGRESS]),
                ),
            )
            .returning(
                JobRun.id,
                JobRun.job_id,
                JobRun.job_schedule_id,
                JobRun.scheduled_at,
                JobRun.assigned_to,
                JobRun.assigned_until,
                JobRun.status,
                JobRun.result,
            )
            .execution_options(
                synchronize_session=False,
            )
        )

        row = (await get_current_session().execute(query)).one_or_none()
        if row is None:
            raise RunAssignmentFailed(f"Failed to assign run {id} to a worker.")

        return JobRunDto(**{k: row[k] for k in row.keys()})

    @transactional
    async def complete_run(self, id: UUID, request: CompleteJobRunDto) -> JobRunDto:
        query = (
            sa.update(
                JobRun,
            )
            .values(
                status=JobRunStatus.COMPLETED,
                result=request.result,
                completed_at=sa.func.now(),
            )
            .where(
                sa.and_(
                    JobRun.id == id,
                    JobRun.status == JobRunStatus.IN_PROGRESS,
                    JobRun.assigned_to == request.worker,
                    JobRun.assigned_until >= sa.func.now(),
                ),
            )
            .returning(
                JobRun.id,
                JobRun.job_id,
                JobRun.job_schedule_id,
                JobRun.scheduled_at,
                JobRun.assigned_to,
                JobRun.assigned_until,
                JobRun.status,
                JobRun.result,
            )
            .execution_options(
                synchronize_session=False,
            )
        )

        row = (await get_current_session().execute(query)).one_or_none()
        if row is None:
            raise RunCompletionFailed(f"Failed to complete run {id}.")

        job_schedule_id = row["job_schedule_id"]
        if job_schedule_id is not None:
            await self._schedule_next_run(job_schedule_id)

        return JobRunDto(**{k: row[k] for k in row.keys()})

    @transactional
    async def schedule_runs(self, schedules: List[JobSchedule]):
        runs = [
            JobRun.create(job=s.job, job_schedule=s, scheduled_at=self._get_next_trigger_time(s.cron))
            for s in schedules
        ]
        get_current_session().add_all(runs)

    async def _schedule_next_run(self, id: UUID):
        session = get_current_session()
        job_schedule = await session.get(JobSchedule, id, options=[sao.joinedload(JobSchedule.job)])

        await self.schedule_runs([job_schedule])

    def _get_next_trigger_time(self, cron: str) -> datetime:
        try:
            schedule = CronTab(cron)
        except ValueError:
            raise InvalidCronExpressionError(f"{cron} is not a valid cron expression.")

        return schedule.next(default_utc=True, return_datetime=True)


class JobService:
    def __init__(self, run_service: JobRunService = Depends(JobRunService)):
        self._run_service = run_service

    async def list_jobs(self, params: JobQueryParamsDto) -> Page[JobDto]:
        query = sa.select(Job).options(sao.selectinload(Job.schedules))
        if params.sort is not None:
            query = query.order_by(params.sort_order.apply(params.sort.column))

        items, count = await get_current_session().get_page(query, offset=params.offset, limit=params.limit)
        return Page(count=count, results=[JobDto.from_orm(j) for j in items])

    async def get_job(self, id: UUID) -> JobDto:
        job = await get_current_session().get(Job, id, options=[sao.selectinload(Job.schedules)])
        if job is None:
            raise NotFoundError(f"Could not find job with id {id}")

        return JobDto.from_orm(job)

    @transactional
    async def create_job(self, request: JobRequestDto) -> JobDto:
        job = Job.create(name=request.name)
        job_schedules = [JobSchedule.create(cron=s.cron, job=job) for s in request.schedules]
        job.schedules = job_schedules

        await self._run_service.schedule_runs(job_schedules)

        get_current_session().add(job)

        return JobDto.from_orm(job)
