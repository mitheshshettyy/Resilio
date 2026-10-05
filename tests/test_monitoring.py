from agent.monitoring import MonitoringPipeline, MonitoringTarget


class FakeRecoveryManager:
    def __init__(self, results=None, error_components=None):
        self.results = results or {}
        self.error_components = error_components or set()
        self.calls = []

    def recover_and_verify(self, component, context=None, **kwargs):
        self.calls.append((component, context, kwargs))
        if component in self.error_components:
            raise RuntimeError(f"{component} recovery failed")
        return self.results.get(
            component,
            {
                "component": component,
                "action_status": "recovered",
                "verification_status": "verified",
            },
        )


def target(component, collector, health_evaluator, recovery_arguments=lambda value: ({}, {})):
    return MonitoringTarget(component, collector, health_evaluator, recovery_arguments)


def test_pipeline_returns_structured_results_for_multiple_components():
    manager = FakeRecoveryManager()
    pipeline = MonitoringPipeline(
        manager,
        [
            target("cpu", lambda: 20, lambda value: "HEALTHY"),
            target("memory", lambda: 95, lambda value: "CRITICAL"),
        ],
    )

    result = pipeline.run()

    assert [item.component for item in result.components] == ["cpu", "memory"]
    assert result.get_component("cpu").measurement == 20
    assert result.get_component("cpu").recovery_required is False
    memory = result.get_component("memory")
    assert memory.health_status == "CRITICAL"
    assert memory.recovery_required is True
    assert memory.recovery_attempted is True
    assert memory.recovery_result["verification_status"] == "verified"
    assert result.to_dict()["components"][1]["timestamp"].endswith("+00:00")


def test_pipeline_does_not_recover_healthy_component():
    manager = FakeRecoveryManager()
    result = MonitoringPipeline(
        manager, [target("cpu", lambda: 20, lambda value: "HEALTHY")]
    ).run()

    assert manager.calls == []
    assert result.get_component("cpu").recovery_result is None


def test_pipeline_isolates_collector_failure():
    def failed_collector():
        raise OSError("cpu unavailable")

    manager = FakeRecoveryManager()
    result = MonitoringPipeline(
        manager,
        [
            target("cpu", failed_collector, lambda value: "HEALTHY"),
            target("memory", lambda: 95, lambda value: "CRITICAL"),
        ],
    ).run()

    cpu = result.get_component("cpu")
    assert cpu.health_status == "UNAVAILABLE"
    assert cpu.error == "cpu unavailable"
    assert manager.calls == [("memory", {}, {})]


def test_pipeline_isolates_recovery_failure():
    manager = FakeRecoveryManager(error_components={"cpu"})
    result = MonitoringPipeline(
        manager,
        [
            target("cpu", lambda: 95, lambda value: "CRITICAL"),
            target("memory", lambda: 20, lambda value: "HEALTHY"),
        ],
    ).run()

    cpu = result.get_component("cpu")
    assert cpu.recovery_required is True
    assert cpu.recovery_attempted is False
    assert cpu.error == "cpu recovery failed"
    assert result.get_component("memory").health_status == "HEALTHY"


def test_pipeline_keeps_unverified_recovery_result():
    manager = FakeRecoveryManager(
        results={
            "disk": {
                "component": "disk",
                "action_status": "recovered",
                "verification_status": "not_verified",
                "reason": "disk usage remains critical",
            }
        }
    )
    result = MonitoringPipeline(
        manager, [target("disk", lambda: 95, lambda value: "CRITICAL")]
    ).run()

    disk = result.get_component("disk")
    assert disk.recovery_attempted is True
    assert disk.recovery_result["verification_status"] == "not_verified"
    assert disk.recovery_result["reason"] == "disk usage remains critical"


def test_pipeline_skips_recovery_without_a_safe_target():
    manager = FakeRecoveryManager()
    result = MonitoringPipeline(
        manager,
        [
            target(
                "process",
                lambda: None,
                lambda value: "CRITICAL",
                lambda value: ({}, None),
            )
        ],
    ).run()

    process = result.get_component("process")
    assert process.health_status == "CRITICAL"
    assert process.recovery_required is False
    assert manager.calls == []
