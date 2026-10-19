"""Scenario file model and loader. Steps are either an `action` or an `assert`."""
import logging
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import AliasChoices, BaseModel, BeforeValidator, ConfigDict, Field, ValidationError

from .config import settings
from .steps import Step, parse_step


logger = logging.getLogger(__name__)

def _parse_steps(values: Any) -> Any:
    if not isinstance(values, list):
        return values
    steps = []
    for index, value in enumerate(values):
        try:
            steps.append(parse_step(value))
        except ValidationError as exc:
            raise ValueError(f"step {index}: {exc.errors(include_url=False)}") from exc
        except ValueError as exc:
            raise ValueError(f"step {index}: {exc}") from exc
    return steps


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    archived: bool = Field(default=False, validation_alias=AliasChoices("archived"))
    steps: Annotated[list[Step], BeforeValidator(_parse_steps)]


class ChallengeNotFound(Exception):
    pass


def challenge_key(path: Path, root: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix().lower()


def discover_challenges() -> dict[str, Scenario]:
    """All valid challenge files below the challenges dir, keyed e.g. `week-0/first-peer`."""
    root = Path(settings.challenges_dir).resolve()
    found: dict[str, Scenario] = {}
    for path in sorted([*root.rglob("*.yml"), *root.rglob("*.yaml")]):
        try:
            found[challenge_key(path, root)] = Scenario.model_validate(yaml.safe_load(path.read_text()))
        except Exception:
            logger.exception("Skipping invalid challenge file %s", path)
    return found


def resolve_challenge_path(challenge: str) -> Path:
    """Map e.g. `week-0/first-peer` to Challenges/Week-0/first-peer.yml (case-insensitive)."""
    root = Path(settings.challenges_dir).resolve()
    current = root
    parts = [p for p in challenge.split("/") if p]
    if not parts or any(p in (".", "..") or "\\" in p for p in parts):
        raise ChallengeNotFound(challenge)
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        wanted = [f"{part}.yml", f"{part}.yaml"] if last else [part]
        match = None
        if current.is_dir():
            for entry in current.iterdir():
                if entry.name.lower() in (w.lower() for w in wanted) and entry.is_dir() != last:
                    match = entry
                    break
        if match is None:
            raise ChallengeNotFound(challenge)
        current = match
    return current


def load_scenario(challenge: str) -> Scenario:
    path = resolve_challenge_path(challenge)
    return Scenario.model_validate(yaml.safe_load(path.read_text()))
