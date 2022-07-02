from datetime import datetime
from datetime import timedelta
from enum import Enum
from typing import Generic, List, TypeVar
from uuid import UUID

import pydantic
from pydantic import generics
from pydantic import validator
import sqlalchemy as sa

from api.config import MAX_RUN_LEASE_DURATION
from api.config import MIN_RUN_LEASE_DURATION
from api.models import Job
from api.models import JobRun
from api.models import JobRunStatus

ItemT = TypeVar("ItemT")


class SortOrder(Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"

    def apply(self, column):
        return sa.asc(column) if self == SortOrder.ASCENDING else sa.desc(column)


class JobSortField(Enum):
    NAME = "name"

    @property
    def column(self):
        if self == JobSortField.NAME:
            return Job.name


class JobRunSortField(Enum):
    SCHEDULED_AT = "scheduled_at"

    @property
    def column(self):
        if self == JobRunSortField.SCHEDULED_AT:
            return JobRun.scheduled_at


class Page(generics.GenericModel, Generic[ItemT]):
    count: int
    results: List[ItemT]


class JobScheduleRequestDto(pydantic.BaseModel):
    cron: str


class JobRequestDto(pydantic.BaseModel):
    name: str
    schedules: List[JobScheduleRequestDto]


class JobScheduleDto(pydantic.BaseModel):
    id: UUID
    job_id: UUID
    cron: str

    class Config:
        orm_mode = True


class JobDto(pydantic.BaseModel):
    id: UUID
    name: str
    schedules: List[JobScheduleDto]

    class Config:
        orm_mode = True


class JobRunDto(pydantic.BaseModel):
    id: UUID
    job_id: UUID
    job_schedule_id: UUID | None
    scheduled_at: datetime | None
    assigned_to: str | None
    assigned_until: datetime | None
    status: JobRunStatus
    result: str | None

    class Config:
        orm_mode = True


class AssignJobRunDto(pydantic.BaseModel):
    worker: str
    lease_duration: timedelta

    @validator("lease_duration")
    def validate_lease_duration(cls, value: timedelta):
        if value < MIN_RUN_LEASE_DURATION:
            raise ValueError(f"Task lease duration must not be less than {MIN_RUN_LEASE_DURATION}.")

        if value > MAX_RUN_LEASE_DURATION:
            raise ValueError(f"Task lease duration must not be greater than {MAX_RUN_LEASE_DURATION}.")

        return value


class CompleteJobRunDto(pydantic.BaseModel):
    worker: str
    result: str


class ErrorResponseDto(pydantic.BaseModel):
    detail: str


class PaginationParamsDto(pydantic.BaseModel):
    offset: int
    limit: int
    sort_order: SortOrder


class JobQueryParamsDto(PaginationParamsDto):
    sort: JobSortField | None


class JobRunQueryParamsDto(PaginationParamsDto):
    sort: JobRunSortField | None
    assignable_only: bool
