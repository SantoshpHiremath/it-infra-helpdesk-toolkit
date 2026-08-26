import socket
import threading
import time

import pytest

from src.infra_monitor import (
    check_disk_usage, check_host_reachable, evaluate_gpu_workstation_reading,
    SimulatedGpuWorkstationReading, HealthStatus,
)


class TestCheckDiskUsage:
    def test_returns_a_real_result_for_root_filesystem(self):
        result = check_disk_usage("/")
        assert result.value is not None
        assert 0 <= result.value <= 100
        assert result.status in (HealthStatus.OK, HealthStatus.WARNING, HealthStatus.CRITICAL)

    def test_low_usage_is_ok(self):
        # Using thresholds far above any realistic usage confirms the OK path.
        result = check_disk_usage("/", warning_threshold_pct=99.9, critical_threshold_pct=99.99)
        assert result.status == HealthStatus.OK

    def test_thresholds_are_actually_applied(self):
        # Using a threshold of 0% guarantees CRITICAL regardless of actual usage --
        # confirms the threshold comparison logic itself, not just the real read.
        result = check_disk_usage("/", warning_threshold_pct=0.0, critical_threshold_pct=0.0)
        assert result.status == HealthStatus.CRITICAL


class TestCheckHostReachable:
    def test_reaches_a_real_local_listening_socket(self):
        # Starts a real local TCP server and confirms the check can
        # actually connect to it -- a genuine socket-level test, not a mock.
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
        server.listen(1)

        def accept_once():
            try:
                conn, _ = server.accept()
                conn.close()
            except OSError:
                pass

        thread = threading.Thread(target=accept_once, daemon=True)
        thread.start()
        time.sleep(0.05)

        result = check_host_reachable("127.0.0.1", port, timeout_seconds=1.0)
        server.close()

        assert result.status == HealthStatus.OK
        assert result.value is not None

    def test_unreachable_port_is_critical(self):
        # Port 1 is a reserved, essentially-never-listening port -- a
        # real connection attempt to it should fail.
        result = check_host_reachable("127.0.0.1", 1, timeout_seconds=1.0)
        assert result.status == HealthStatus.CRITICAL
        assert result.value is None


class TestEvaluateGpuWorkstationReading:
    def test_normal_reading_is_ok(self):
        reading = SimulatedGpuWorkstationReading(
            hostname="gpu-ws-01", gpu_utilization_pct=45.0, gpu_memory_used_pct=50.0, temperature_celsius=65.0)
        result = evaluate_gpu_workstation_reading(reading)
        assert result.status == HealthStatus.OK

    def test_high_temperature_below_critical_is_warning(self):
        reading = SimulatedGpuWorkstationReading(
            hostname="gpu-ws-01", gpu_utilization_pct=90.0, gpu_memory_used_pct=60.0, temperature_celsius=85.0)
        result = evaluate_gpu_workstation_reading(reading)
        assert result.status == HealthStatus.WARNING

    def test_critical_temperature_is_critical(self):
        reading = SimulatedGpuWorkstationReading(
            hostname="gpu-ws-01", gpu_utilization_pct=95.0, gpu_memory_used_pct=70.0, temperature_celsius=92.0)
        result = evaluate_gpu_workstation_reading(reading)
        assert result.status == HealthStatus.CRITICAL

    def test_high_memory_usage_alone_triggers_warning(self):
        reading = SimulatedGpuWorkstationReading(
            hostname="gpu-ws-01", gpu_utilization_pct=20.0, gpu_memory_used_pct=95.0, temperature_celsius=55.0)
        result = evaluate_gpu_workstation_reading(reading)
        assert result.status == HealthStatus.WARNING

    def test_critical_takes_precedence_over_warning_conditions(self):
        reading = SimulatedGpuWorkstationReading(
            hostname="gpu-ws-01", gpu_utilization_pct=99.0, gpu_memory_used_pct=99.0, temperature_celsius=95.0)
        result = evaluate_gpu_workstation_reading(reading)
        assert result.status == HealthStatus.CRITICAL
