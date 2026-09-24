"""Local application launching service for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import platform
import subprocess

from nayeon.services.application_observation import (
    ApplicationDefinition, ApplicationObservation, ApplicationState,
    DEFAULT_APPLICATIONS, windows_process_names,
)


@dataclass(frozen=True)
class LaunchResult:
    """Result of an application launch attempt."""

    success: bool
    target: str
    message: str


class ApplicationService:
    """Launch local applications in a controlled, platform-aware way."""

    def __init__(self, *, applications: tuple[ApplicationDefinition, ...] = DEFAULT_APPLICATIONS) -> None:
        self._applications: dict[str, ApplicationDefinition] = {}
        for definition in applications:
            for target in definition.targets:
                if target in self._applications:
                    raise ValueError("Ambiguous application observation target.")
                self._applications[target] = definition

    def observe(self, target: str) -> ApplicationObservation:
        """Observe only an explicitly configured identity; never infer from text."""
        unknown = ApplicationObservation(target, ApplicationState.UNKNOWN)
        if not isinstance(target, str) or platform.system() != "Windows":
            return unknown
        definition = self._applications.get(target.casefold())
        if definition is None or not definition.expected_process_names:
            return unknown
        try:
            names = windows_process_names()
            if (not isinstance(names, frozenset) or not names
                    or any(not isinstance(name, str) or not name for name in names)):
                return unknown
            observed = bool(set(definition.expected_process_names) & {name.casefold() for name in names})
            state = ApplicationState.OBSERVED_OPEN if observed else ApplicationState.OBSERVED_CLOSED
            return ApplicationObservation(target, state, definition.application_id,
                                          definition.expected_process_names)
        except Exception:
            return unknown

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
