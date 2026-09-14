"""Local application launching service for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import platform
import subprocess


@dataclass(frozen=True)
class LaunchResult:
    """Result of an application launch attempt."""

    success: bool
    target: str
    message: str


class ApplicationService:
    """Launch local applications in a controlled, platform-aware way."""

    def launch(self, target: str) -> LaunchResult:
        """Launch an application by name or executable path."""

        target = target.strip()

        if not target:
            return LaunchResult(
                success=False,
                target=target,
                message="Application target cannot be empty.",
            )

        system = platform.system()

        try:
            if system == "Windows":
                return self._launch_windows(target)

            if system == "Darwin":
                subprocess.Popen(
                    ["open", "-a", target],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return LaunchResult(
                    success=True,
                    target=target,
                    message=f"Launched {target}.",
                )

            if system == "Linux":
                subprocess.Popen(
                    [target],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return LaunchResult(
                    success=True,
                    target=target,
                    message=f"Launched {target}.",
                )

            return LaunchResult(
                success=False,
                target=target,
                message=f"Unsupported operating system: {system}.",
            )

        except (OSError, FileNotFoundError) as error:
            return LaunchResult(
                success=False,
                target=target,
                message=f"Could not launch {target}: {error}",
            )

    def _launch_windows(self, target: str) -> LaunchResult:
        """Launch an application on Windows."""

        path = Path(target)

        if path.exists():
            os.startfile(path)
            return LaunchResult(
                success=True,
                target=target,
                message=f"Launched {target}.",
            )

        # Start-menu/application aliases can often be resolved by Windows
        # without shell=True.
        try:
            subprocess.Popen(
                [target],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return LaunchResult(
                success=True,
                target=target,
                message=f"Launched {target}.",
            )

        except (OSError, FileNotFoundError) as error:
            return LaunchResult(
                success=False,
                target=target,
                message=f"Could not launch {target}: {error}",
            )