"""Name -> step class registries filled by the `@action` / `@assertion` decorators."""
from typing import Any, Callable

from .base import Step

ACTIONS: dict[str, type[Step]] = {}
ASSERTIONS: dict[str, type[Step]] = {}


def _register(kind: str, registry: dict[str, type[Step]], name: str) -> Callable[[type[Step]], type[Step]]:
    def decorator(cls: type[Step]) -> type[Step]:
        if name in registry:
            raise ValueError(f"Duplicate {kind} {name!r}")
        cls.kind = kind  # type: ignore[assignment]
        cls.name = name
        registry[name] = cls
        return cls

    return decorator


def action(name: str):
    return _register("action", ACTIONS, name)


def assertion(name: str):
    return _register("assert", ASSERTIONS, name)


def parse_step(value: Any) -> Step:
    """Turn a raw YAML step (`{action: x, ...}` or `{assert: x, ...}`) into a Step instance."""
    if isinstance(value, Step):
        return value
    if not isinstance(value, dict):
        raise ValueError("a step must be a mapping")
    data = dict(value)
    has_action, has_assert = "action" in data, "assert" in data
    if has_action == has_assert:
        raise ValueError("a step needs exactly one of 'action' or 'assert'")
    key, registry = ("action", ACTIONS) if has_action else ("assert", ASSERTIONS)
    name = data.pop(key)
    cls = registry.get(name)
    if cls is None:
        raise ValueError(f"unknown {key} {name!r}; known: {sorted(registry)}")
    return cls.model_validate(data)
