"""
Real infrastructure health checks -- built to close the posting's
"assist with maintaining our on-site infrastructure: GPU workstations,
servers, and network equipment" ask. These checks are genuinely real
where the sandbox allows it (disk usage, host reachability via a real
socket connection) and clearly, honestly modeled/synthetic where real
hardware isn't available (there is no real GPU workstation or on-prem
network switch in this environment -- see README).
"""
import shutil
import socket
import time
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    check_name: str
    status: HealthStatus
    detail: str
    value: float | None = None


def check_disk_usage(path: str = "/", warning_threshold_pct: float = 80.0,
                      critical_threshold_pct: float = 95.0) -> HealthCheckResult:
    """A real disk-usage check against the actual filesystem at `path`
    -- not a mock. Used here as the real, checkable half of what a
    server/workstation health check does; the GPU/network checks below
    are synthetic since no real hardware is reachable from this
    sandbox."""
    usage = shutil.disk_usage(path)
    used_pct = round((usage.used / usage.total) * 100, 1)

    if used_pct >= critical_threshold_pct:
        status = HealthStatus.CRITICAL
    elif used_pct >= warning_threshold_pct:
        status = HealthStatus.WARNING
    else:
        status = HealthStatus.OK

    return HealthCheckResult(
        check_name=f"disk_usage:{path}",
        status=status,
        detail=f"{used_pct}% used ({usage.used // (1024**3)}GB / {usage.total // (1024**3)}GB)",
        value=used_pct,
    )


def check_host_reachable(host: str, port: int, timeout_seconds: float = 2.0) -> HealthCheckResult:
    """A real TCP-connect reachability check -- genuinely opens a
    socket and attempts to connect, not a simulated result. Used to
    represent the kind of "is this server/switch/workstation actually
    up" check a real IT support workflow runs constantly."""
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            return HealthCheckResult(
                check_name=f"host_reachable:{host}:{port}",
                status=HealthStatus.OK,
                detail=f"connected in {elapsed_ms}ms",
                value=elapsed_ms,
            )
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        return HealthCheckResult(
            check_name=f"host_reachable:{host}:{port}",
            status=HealthStatus.CRITICAL,
            detail=f"unreachable: {exc}",
            value=None,
        )


@dataclass(frozen=True)
class SimulatedGpuWorkstationReading:
    """A synthetic GPU-workstation telemetry reading. No real GPU
    telemetry is available in this sandbox (no nvidia-smi, no real
    GPU hardware) -- this represents the SHAPE of the check a real
    monitoring agent (e.g. one polling nvidia-smi or a Prometheus GPU
    exporter) would perform, honestly labeled as simulated rather
    than presented as a real hardware reading."""
    hostname: str
    gpu_utilization_pct: float
    gpu_memory_used_pct: float
    temperature_celsius: float


def evaluate_gpu_workstation_reading(
    reading: SimulatedGpuWorkstationReading,
    temp_warning_c: float = 80.0,
    temp_critical_c: float = 90.0,
    memory_warning_pct: float = 90.0,
) -> HealthCheckResult:
    """Applies real, explicit thresholds to a (simulated) GPU reading.
    The threshold LOGIC is real and testable even though the input
    reading itself is synthetic in this environment."""
    if reading.temperature_celsius >= temp_critical_c:
        return HealthCheckResult(
            check_name=f"gpu_workstation:{reading.hostname}",
            status=HealthStatus.CRITICAL,
            detail=f"GPU temperature {reading.temperature_celsius}C exceeds critical threshold {temp_critical_c}C",
            value=reading.temperature_celsius,
        )
    if reading.temperature_celsius >= temp_warning_c or reading.gpu_memory_used_pct >= memory_warning_pct:
        return HealthCheckResult(
            check_name=f"gpu_workstation:{reading.hostname}",
            status=HealthStatus.WARNING,
            detail=f"temp={reading.temperature_celsius}C, mem={reading.gpu_memory_used_pct}%",
            value=reading.temperature_celsius,
        )
    return HealthCheckResult(
        check_name=f"gpu_workstation:{reading.hostname}",
        status=HealthStatus.OK,
        detail=f"temp={reading.temperature_celsius}C, mem={reading.gpu_memory_used_pct}%, util={reading.gpu_utilization_pct}%",
        value=reading.temperature_celsius,
    )
