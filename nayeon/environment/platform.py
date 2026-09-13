"""Nayeon platform detection and basic platform metadata."""

from __future__ import annotations

from dataclasses import dataclass
import platform as _platform
import sys


@dataclass(frozen=True)
class PlatformInfo:
    """Immutable description of the machine running Nayeon."""

    system: str
    release: str
    version: str
    machine: str
    python_version: str

    @property
    def is_windows(self) -> bool:
        return self.system == "Windows"

    @property
    def is_macos(self) -> bool:
        return self.system == "Darwin"

    @property
    def is_linux(self) -> bool:
        return self.system == "Linux"

    @property
    def is_supported(self) -> bool:
        return self.system in {"Windows", "Darwin", "Linux"}


def get_platform_info() -> PlatformInfo:
    """Return information about the machine running Nayeon."""

    return PlatformInfo(
        system=_platform.system(),
        release=_platform.release(),
        version=_platform.version(),
        machine=_platform.machine(),
        python_version=sys.version.split()[0],
    )