import json
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Certification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    trade: str
    org_id: Optional[int] = Field(default=None, foreign_key="organisation.id")
    custom_rubric_id: Optional[int] = Field(default=None, foreign_key="customrubric.id")
    status: str = Field(default="in_progress")  # in_progress | passed | failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    certification_id: int = Field(foreign_key="certification.id")
    task_id: str  # T1-T5 or P1-P5
    file_path: Optional[str] = None
    video_url: Optional[str] = None
    assessment_json: str = Field(default="{}")
    safety_score: float = 0
    technique_score: float = 0
    result_score: float = 0
    weighted_total: float = 0
    passed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def assessment(self) -> dict:
        return json.loads(self.assessment_json)


class Organisation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    logo_url: Optional[str] = None
    slug: str = Field(unique=True, index=True)  # URL-friendly identifier
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CustomRubric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organisation.id")
    trade: str  # base trade template (tiling, painting)
    rubric_json: str = Field(default="{}")  # full customised rubric
    pass_threshold: float = 70
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def rubric(self) -> dict:
        return json.loads(self.rubric_json)


class Certificate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    certification_id: int = Field(foreign_key="certification.id")
    cert_id: str = Field(unique=True, index=True)
    worker_name: str
    trade: str
    overall_score: float
    safety_score: float
    technique_score: float
    result_score: float
    org_name: Optional[str] = None
    pdf_path: str
    verify_url: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="valid")  # valid | expired | revoked
