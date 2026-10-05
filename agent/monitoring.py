"""Monitoring pipeline orchestration and structured cycle results."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


logger = logging.getLogger(__name__)


@dataclass
class ComponentMonitoringResult:
    """The observable outcome for one monitored component."""

    component: str
    measurement: Any = None
    health_status: str = "UNAVAILABLE"
    recovery_required: bool = False
    recovery_attempted: bool = False
    recovery_result: dict[str, Any] | None = None
    error: str | None = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a serialization-friendly representation of this result."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class MonitoringCycleResult:
    """Structured outcome of a complete monitoring cycle."""

    components: list[ComponentMonitoringResult]
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def get_component(self, component: str) -> ComponentMonitoringResult:
        """Return the result for a named component."""
        return next(item for item in self.components if item.component == component)

    def to_dict(self) -> dict[str, Any]:
        """Return a serialization-friendly representation of this cycle."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "components": [result.to_dict() for result in self.components],
        }


@dataclass(frozen=True)
class MonitoringTarget:
    """Collection, evaluation, and safe recovery inputs for one component."""

    component: str
    collector: Callable[[], Any]
    health_evaluator: Callable[[Any], str]
    recovery_arguments: Callable[
        [Any], tuple[dict[str, Any], dict[str, Any] | None]
    ]


class MonitoringPipeline:
    """Run collection, health evaluation, and recovery independently per target."""

    def __init__(self, recovery_manager: Any, targets: list[MonitoringTarget]) -> None:
        self._recovery_manager = recovery_manager
        self._targets = targets

    def run(self) -> MonitoringCycleResult:
        """Run one cycle without allowing one component to stop another."""
        return MonitoringCycleResult(
            components=[self._monitor_target(target) for target in self._targets]
        )

    def _monitor_target(self, target: MonitoringTarget) -> ComponentMonitoringResult:
        try:
            measurement = target.collector()
        except Exception as error:
            logger.exception("Collection failed for component=%s", target.component)
            return ComponentMonitoringResult(
                component=target.component,
                error=str(error),
            )

        try:
            health_status = target.health_evaluator(measurement)
        except Exception as error:
            logger.exception(
                "Health evaluation failed for component=%s", target.component
            )
            return ComponentMonitoringResult(
                component=target.component, measurement=measurement, error=str(error)
            )

        result = ComponentMonitoringResult(
            component=target.component,
            measurement=measurement,
            health_status=health_status,
        )
        if health_status != "CRITICAL":
            return result

        try:
            context, kwargs = target.recovery_arguments(measurement)
        except Exception as error:
            logger.exception(
                "Recovery decision failed for component=%s", target.component
            )
            result.error = str(error)
            return result
        if kwargs is None:
            return result

        result.recovery_required = True
        try:
            recovery_result = self._recovery_manager.recover_and_verify(
                target.component, context=context, **kwargs
            )
        except Exception as error:
            logger.exception("Recovery failed for component=%s", target.component)
            result.error = str(error)
            return result

        result.recovery_result = recovery_result
        result.recovery_attempted = (
            recovery_result.get("action_status") != "not_attempted"
        )
        return result
