import uuid
from datetime import datetime
from enum import Enum

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sap
import sqlalchemy.orm as sao

Base = sao.declarative_base()


class JobRunStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Job(Base):
    __tablename__ = "jobs"

    id = sa.Column(sap.UUID(as_uuid=True), primary_key=True)
    name = sa.Column(sa.String(length=100))

    schedules = sao.relationship("JobSchedule", back_populates="job")
    runs = sao.relationship("JobRun", back_populates="job")

    @classmethod
    def create(cls, name: str) -> "Job":
        return cls(id=uuid.uuid4(), name=name)


class JobSchedule(Base):
    __tablename__ = "job_schedules"

    id = sa.Column(sap.UUID(as_uuid=True), primary_key=True)
    job_id = sa.Column(sa.ForeignKey("jobs.id"), index=True)
    cron = sa.Column(sa.String(length=100))

    job = sao.relationship("Job", back_populates="schedules")
    runs = sao.relationship("JobRun", back_populates="schedule")

    @classmethod
    def create(cls, cron: str, job: Job) -> "JobSchedule":
        return cls(id=uuid.uuid4(), job_id=job.id, job=job, cron=cron)


class JobRun(Base):
    __tablename__ = "job_runs"

    id = sa.Column(sap.UUID(as_uuid=True), primary_key=True)
    job_id = sa.Column(sa.ForeignKey("jobs.id"), index=True)
    job_schedule_id = sa.Column(sa.ForeignKey("job_schedules.id"), nullable=True)
    scheduled_at = sa.Column(sa.DateTime, index=True)
    completed_at = sa.Column(sa.DateTime, nullable=True)
    assigned_to = sa.Column(sa.String(length=100), nullable=True)
    assigned_until = sa.Column(sa.DateTime, nullable=True)
    status = sa.Column(sa.Enum(JobRunStatus))
    result = sa.Column(sa.Text, nullable=True)

    job = sao.relationship("Job", back_populates="runs")
    schedule = sao.relationship("JobSchedule", back_populates="runs")

    @classmethod
    def create(
            cls,
            job: Job,
            job_schedule: JobSchedule | None = None,
            scheduled_at: datetime | None = None,
    ) -> "JobRun":
        return cls(
            id=uuid.uuid4(),
            job_id=job.id,
            job_schedule_id=job_schedule.id if job_schedule is not None else None,
            scheduled_at=scheduled_at,
            completed_at=None,
            job=job,
            schedule=job_schedule,
            status=JobRunStatus.SCHEDULED,
            result=None,
        )
