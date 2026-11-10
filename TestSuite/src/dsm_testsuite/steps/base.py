"""Step base class, execution context and step errors."""
from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict

from ..clients import OrchestratorClient, ProxyClient
from ..model import ChordModel


class StepError(Exception):
    """An action could not be carried out (infrastructure problem -> run status `error`)."""


class AssertionFailed(Exception):
    """An assertion does not hold (-> run status `failed`)."""


@dataclass
class StepContext:
    network_id: str
    orchestrator: OrchestratorClient
    proxy: ProxyClient
    # Flag if fingers need to be checked
    check_fingers: bool = field(default=False)
    # Peers started by this run and not yet stopped; killed on cleanup.
    started_peers: set[str] = field(default_factory=set)
    # Ring the network is expected to have, updated by the join/leave/stop actions.
    model: ChordModel = field(default_factory=ChordModel)


class Step(BaseModel):
    """Subclass, declare the YAML parameters as fields, implement `execute`, and register
    the class with `@action("name")` or `@assertion("name")`."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    kind: ClassVar[Literal["action", "assert"]]
    name: ClassVar[str]

    async def execute(self, ctx: StepContext) -> None:
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {"kind": self.kind, "name": self.name, "params": self.model_dump(by_alias=True)}
