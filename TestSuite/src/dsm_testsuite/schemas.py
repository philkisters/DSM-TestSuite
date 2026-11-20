from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from ipaddress import ip_address
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from dsm_protocol import OrchestratorProtocolVersion


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
    color: str
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
    """Pushed over the health websocket after every health check cycle."""

    group_id: int
    state: str
    failures: int
    since: datetime | None = None
    uptime_seconds: float = 0.0
    downtime_seconds: float = 0.0
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


class Network(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    network_id: str
    orchestrator_version: OrchestratorProtocolVersion
    replication_factor: int | None = None
    created_at: datetime


class NetworkCreate(BaseModel):
    network_id: str = Field(min_length=1, max_length=128)
    orchestrator_version: OrchestratorProtocolVersion = OrchestratorProtocolVersion.V1
    replication_factor: int | None = Field(default=None, gt=0)

    @field_validator("network_id")
    @classmethod
    def _strip_network_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("network_id must not be blank")
        return value

    def model_post_init(self, _context: object) -> None:
        if (
            self.orchestrator_version is OrchestratorProtocolVersion.V1
            and self.replication_factor is not None
        ):
            raise ValueError("replication_factor requires orchestrator version v2")


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
    
    @property
    def duration_seconds(self) -> float | None:
        """Calculate run duration in seconds; returns None if not finished."""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
    
    @property
    def message_count(self) -> int | None:
        """Get message count from metrics; returns None if not recorded."""
        if self.metrics and "message_count" in self.metrics:
            return self.metrics["message_count"]
        return None


class GroupChallengeResult(BaseModel):
    status: Literal["passed", "failed"]
    timestamp: datetime | None = None
    first_success: tuple[int | None, float | None, datetime] | None = None
    lowest_message_count: tuple[int, float | None, datetime] | None = None
    shortest_duration: tuple[int | None, float, datetime] | None = None


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


class RunError(BaseModel):
    """core.run_errors - HTTP errors when communicating with Orchestrator/Proxy"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    step_index: int
    name: str
    params: dict
    error_code: int | None
    error_text: str
    created_at: datetime


class RunEventResult(BaseModel):
    """Unified schema for assertion and error events."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    step_index: int
    name: str
    params: dict
    created_at: datetime
    type: Literal["assertion", "error"]
    passed: bool | None = None
    message: str | None = None
    error_code: int | None = None
    error_text: str | None = None
    
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


class CategoryRankings(BaseModel):
    """Rankings for a specific category (time, duration, messages) across all groups."""
    first_place: int | None = Field(None, description="Group ID with first place")
    second_place: int | None = Field(None, description="Group ID with second place")
    third_place: int | None = Field(None, description="Group ID with third place")


class ChallengeCategoryStats(BaseModel):
    """Statistics for a single challenge in a specific category."""
    key: str = Field(description="Challenge key")
    title: str = Field(description="Challenge title")
    week: str = Field(description="Week extracted from key")
    passed_count: int = Field(description="Number of groups that passed this challenge")
    time_rankings: CategoryRankings = Field(description="Rankings for fastest completion")
    duration_rankings: CategoryRankings = Field(description="Rankings for shortest duration")
    messages_rankings: CategoryRankings = Field(description="Rankings for fewest messages")


class GroupChallengeOverview(BaseModel):
    """Overview of a group's performance across all challenges."""
    group_id: int
    group_name: str
    group_color: str
    total_passed_challenges: int = Field(description="Total number of challenges passed")
    first_places: dict[str, int] = Field(description="Category (time/duration/messages) -> count")
    second_places: dict[str, int] = Field(description="Category (time/duration/messages) -> count")
    third_places: dict[str, int] = Field(description="Category (time/duration/messages) -> count")
    challenges_by_status: list[GroupChallengeStats] = Field(description="Stats for each challenge")