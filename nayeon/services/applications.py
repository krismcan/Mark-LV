"""Local application launching service for Nayeon."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
import os
import platform
import subprocess
import time

from nayeon.services.application_observation import (
    ApplicationDefinition, ApplicationObservation, ApplicationState,
    ApplicationIdentity, ProcessIdentity, normalize_executable_path,
    ApplicationReadinessPolicy, DEFAULT_APPLICATIONS, windows_process_identities,
)
import ntpath


@dataclass(frozen=True)
class LaunchResult:
    """Result of an application launch attempt."""

    success: bool
    target: str
    message: str


class ApplicationService:
    """Launch local applications in a controlled, platform-aware way."""

    def __init__(
        self, *, applications: tuple[ApplicationDefinition, ...] = DEFAULT_APPLICATIONS,
        readiness: ApplicationReadinessPolicy = ApplicationReadinessPolicy(),
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if not isinstance(readiness, ApplicationReadinessPolicy) or not callable(sleeper):
            raise TypeError("Application readiness requires a policy and callable sleeper.")
        self._readiness = readiness
        self._sleeper = sleeper
        self._applications: dict[str, ApplicationDefinition] = {}
        for definition in applications:
            for target in definition.targets:
                if target in self._applications:
                    raise ValueError("Ambiguous application observation target.")
                self._applications[target] = definition

    def observe(self, target: str) -> ApplicationObservation:
        """Retain one-shot observation without waits or launch side effects."""
        definition = self._observation_definition(target)
        if definition is None:
            return ApplicationObservation(target, ApplicationState.UNKNOWN)
        return self._observe_definition(target, definition)

    def _observation_definition(self, target: str) -> ApplicationDefinition | None:
        if not isinstance(target, str) or platform.system() != "Windows":
            return None
        definition = self._applications.get(target.casefold())
        if (definition is None or not definition.expected_process_names
                or not definition.accepted_executable_paths):
            return None
        return definition

    def observe_readiness(self, target: str) -> ApplicationObservation:
        """Give one successful launch a short opportunity to become observable.

        Pin metadata once. Match ends immediately; only mismatches on every
        attempt justify the existing candidate-negative result. No launch,
        request interpretation, audit events, or persistent timing state here.
        """
        unknown = ApplicationObservation(target, ApplicationState.UNKNOWN)
        try:
            definition = self._observation_definition(target)
            if definition is None:
                return unknown
            policy, sleeper = self._readiness, self._sleeper
            all_mismatched = True
            for attempt in range(policy.max_attempts):
                observation = self._observe_definition(target, definition)
                if (not isinstance(observation, ApplicationObservation)
                        or observation.target != target
                        or observation.application_id != definition.application_id
                        or observation.expected_process_names != definition.expected_process_names
                        or not isinstance(observation.state, ApplicationState)
                        or not isinstance(observation.identity, ApplicationIdentity)
                        or observation.state is ApplicationState.UNKNOWN
                        or (observation.state is ApplicationState.OBSERVED_CLOSED
                            and observation.identity is not ApplicationIdentity.UNKNOWN)):
                    return unknown
                if observation.identity is ApplicationIdentity.MATCHED:
                    return observation
                all_mismatched &= observation.identity is ApplicationIdentity.MISMATCHED
                if attempt + 1 < policy.max_attempts and policy.delay_seconds:
                    sleeper(policy.delay_seconds)
            return observation if all_mismatched else unknown
        except Exception:
            # OS/provider/sleeper errors never create negative evidence or leak text.
            return unknown

    def _observe_definition(self, target: str, definition: ApplicationDefinition) -> ApplicationObservation:
        """One read-only identity check against the caller's pinned metadata."""
        unknown = ApplicationObservation(target, ApplicationState.UNKNOWN)
        try:
            candidates = windows_process_identities(definition.expected_process_names)
            if not isinstance(candidates, tuple):
                return unknown
            matched, unavailable = False, False
            for candidate in candidates:
                if (not isinstance(candidate, ProcessIdentity)
                        or candidate.name not in definition.expected_process_names):
                    return unknown
                try:
                    path = normalize_executable_path(candidate.executable_path)
                    if ntpath.basename(path).casefold() != candidate.name:
                        # A changed/inconsistent process identity is not a trustworthy mismatch.
                        unavailable = True
                        continue
                except ValueError:
                    unavailable = True
                    continue
                matched |= path in definition.accepted_executable_paths
            state = ApplicationState.OBSERVED_OPEN if candidates else ApplicationState.OBSERVED_CLOSED
            identity = (ApplicationIdentity.MATCHED if matched else
                        ApplicationIdentity.MISMATCHED if candidates and not unavailable else
                        ApplicationIdentity.UNKNOWN)
            return ApplicationObservation(target, state, definition.application_id,
                                          definition.expected_process_names, identity)
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
