"""Runs a scenario's steps sequentially and reports progress through callbacks."""
import logging
from typing import Awaitable, Callable

from .clients import ClientError
from .scenario import Scenario
from .schemas import RunStatus
from .steps import AssertionFailed, HTTPError, StepContext, StepError

logger = logging.getLogger(__name__)

StepReporter = Callable[[int, dict, bool, str | None, int | None], Awaitable[None]]
"""(step index, step description, passed, message, http_status_code)"""


async def execute_scenario(scenario: Scenario, ctx: StepContext, report: StepReporter) -> RunStatus:
    """FAILED if an assertion fails, ERROR if an action/infrastructure call breaks, else PASSED."""
    try:
        for index, step in enumerate(scenario.steps):
            description = step.describe()
            try:
                await step.execute(ctx)
            except AssertionFailed as exc:
                await report(index, description, False, str(exc), None)
                return RunStatus.FAILED
            except HTTPError as exc:
                await report(index, description, False, str(exc), exc.status_code)
                return RunStatus.ERROR
            except (StepError, ClientError) as exc:
                await report(index, description, False, str(exc), None)
                return RunStatus.ERROR
            await report(index, description, True, None, None)
        return RunStatus.PASSED
    except Exception:
        logger.exception("Unexpected error while executing scenario")
        return RunStatus.ERROR
    finally:
        await _cleanup(ctx)


async def _cleanup(ctx: StepContext) -> None:
    for peer in sorted(ctx.started_peers):
        try:
            await ctx.orchestrator.kill(peer)
        except Exception:
            logger.warning("Could not stop peer %r during cleanup", peer, exc_info=True)
    ctx.started_peers.clear()
