"""Basic Nayeon environment diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

from .platform import PlatformInfo, get_platform_info


@dataclass(frozen=True)
class DiagnosticResult:
    """Result of a single environment health check."""

    name: str
    ok: bool
    message: str


def run_basic_diagnostics() -> list[DiagnosticResult]:
    """Run the initial Nayeon environment checks."""

    info: PlatformInfo = get_platform_info()

    return [
        DiagnosticResult(
            name="platform",
            ok=info.is_supported,
            message=(
                f"{info.system} {info.release} ({info.machine})"
                if info.is_supported
                else f"Unsupported platform: {info.system or 'unknown'}"
            ),
        ),
        DiagnosticResult(
            name="python",
            ok=True,
            message=f"Python {info.python_version}",
        ),
    ]