from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from ipaddress import ip_address
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"

class Group(BaseModel):
    """core.groups"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    vm_ip: str | None = None
    created_at: datetime


class GroupHealthStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    state: str
    failures: int
    timestamp: datetime


class GroupUptime(BaseModel):
    group_id: int
    since: datetime | None
    as_of: datetime
    uptime_seconds: float
    downtime_seconds: float
    uptime_percentage: float | None
    downtime_percentage: float | None


class GroupHealthEvent(BaseModel):
    """Pushed over the health websocket whenever a group's state changes."""

    group_id: int
    state: str
    failures: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GroupCreate(BaseModel):
    name: str = Field(min_length=1)
    vm_ip: str = Field(description="IP address of the group's VM")

    @field_validator("name")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("vm_ip")
    @classmethod
    def _ip(cls, v: str) -> str:
        return str(ip_address(v.strip()))


class Challenge(BaseModel):
    """core.challenges"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str = Field(description="Key representing the folder structure, e.g. 'week-0/first-peer'")
    title: str
    steps: int
    description: str | None = None
    archived: bool = False


class RunCreate(BaseModel):
    group_id: int = Field(description="Group ID")
    challenge_id: int = Field(description="Challenge ID")


class Run(BaseModel):
    """core.runs"""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    group_id: int
    challenge_id: int
    network_id: str | None = Field(
        default=None, description="Generated per run to avoid collisions in the proxy"
    )
    seed: int | None = None
    status: RunStatus = RunStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    metrics: dict | None = None


class GroupChallengeResult(BaseModel):
    status: Literal["passed", "failed"]
    timestamp: datetime | None = None


class ChallengeResults(BaseModel):
    group_results: dict[int, GroupChallengeResult] = Field(description="group id -> result")
    run_results: list[Run] = Field(description="All runs of the given group for the challenge")


class RunEvent(BaseModel):
    run_id: str
    type: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RunAssertion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    step_index: int
    name: str
    params: dict
    passed: bool
    message: str | None = None
    created_at: datetime
    
class GroupChallengeStats(BaseModel):
    key: str
    week: str
    title: str
    tries: int
    successes: int
    first_pass: datetime | None = None
    last_fail: datetime | None = None
    
class GroupChallengeStatsResults(BaseModel):
    group_id: int
    stats: list[GroupChallengeStats] = Field(description="List of all group challenge stats")