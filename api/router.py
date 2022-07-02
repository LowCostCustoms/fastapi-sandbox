from uuid import UUID

from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends

from api.dto import AssignJobRunDto
from api.dto import CompleteJobRunDto
from api.dto import JobDto
from api.dto import JobQueryParamsDto
from api.dto import JobRequestDto
from api.dto import JobRunDto
from api.dto import JobRunQueryParamsDto
from api.dto import JobRunSortField
from api.dto import JobSortField
from api.dto import Page
from api.dto import PaginationParamsDto
from api.dto import SortOrder
from api.services import JobRunService
from api.services import JobService

router = APIRouter()

job_tags = ["Job"]
run_tags = ["JobRun"]


def get_pagination_params(
    offset: int = 0,
    limit: int = 100,
    sort_order: SortOrder = SortOrder.ASCENDING,
) -> PaginationParamsDto:
    return PaginationParamsDto(offset=offset, limit=limit, sort_order=sort_order)


def get_job_query_params(
    base: PaginationParamsDto = Depends(get_pagination_params),
    sort: JobSortField | None = None,
) -> JobQueryParamsDto:
    return JobQueryParamsDto(offset=base.offset, limit=base.limit, sort_order=base.sort_order, sort=sort)


def get_job_run_query_params(
    base: PaginationParamsDto = Depends(get_pagination_params),
    sort: JobRunSortField | None = None,
    assignable_only: bool = False,
) -> JobRunQueryParamsDto:
    return JobRunQueryParamsDto(
        offset=base.offset,
        limit=base.limit,
        sort_order=base.sort_order,
        sort=sort,
        assignable_only=assignable_only,
    )


@router.get("/v1/jobs", response_model=Page[JobDto], tags=job_tags)
async def list_jobs(
    params: JobQueryParamsDto = Depends(get_job_query_params),
    service: JobService = Depends(JobService),
) -> Page[JobDto]:
    return await service.list_jobs(params)


@router.get("/v1/jobs/{id}", response_model=JobDto, tags=job_tags)
async def get_job(id: UUID, service: JobService = Depends(JobService)) -> JobDto:
    return await service.get_job(id)


@router.post("/v1/jobs", response_model=JobDto, tags=job_tags)
async def create_job(request: JobRequestDto = Body(), service: JobService = Depends(JobService)) -> JobDto:
    return await service.create_job(request)


@router.get("/v1/runs", response_model=Page[JobRunDto], tags=run_tags)
async def list_runs(
    params: JobRunQueryParamsDto = Depends(get_job_run_query_params),
    service: JobRunService = Depends(JobRunService),
) -> Page[JobRunDto]:
    return await service.list_runs(params)


@router.get("/v1/runs/{id}", response_model=JobRunDto, tags=run_tags)
async def get_run(id: UUID, service: JobRunService = Depends(JobRunService)) -> JobRunDto:
    return await service.get_run(id)


@router.post("/v1/runs/{id}/assign", response_model=JobRunDto, tags=run_tags)
async def assign_run(
    id: UUID,
    request: AssignJobRunDto = Body(),
    service: JobRunService = Depends(JobRunService),
) -> JobRunDto:
    return await service.assign_run(id, request)


@router.post("/v1/runs/{id}/complete", response_model=JobRunDto, tags=run_tags)
async def complete_run(
    id: UUID,
    request: CompleteJobRunDto = Body(),
    service: JobRunService = Depends(JobRunService),
) -> JobRunDto:
    return await service.complete_run(id, request)
