"""Nayeon configuration service.

Handles non-secret application settings.
Secrets such as API keys will be handled separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from threading import RLock
from typing import Any


@dataclass
class NayeonConfig:
    """User and application configuration."""

    assistant_name: str = "Nayeon"
    user_name: str = "Kris"

    wake_word_enabled: bool = False
    morning_briefing_enabled: bool = True
    proactive_enabled: bool = True

    settings: dict[str, Any] = field(default_factory=dict)


class ConfigService:
    """Load, access, and save Nayeon's non-secret configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[2]

        self._config_path = config_path or (
            project_root / "data" / "config.json"
        )

        self._lock = RLock()
        self._config = NayeonConfig()

        self.load()

    @property
    def path(self) -> Path:
        """Return the configuration file path."""

        return self._config_path

    def load(self) -> None:
        """Load configuration from disk when a config file exists."""

        with self._lock:
            if not self._config_path.exists():
                return

            try:
                data = json.loads(
                    self._config_path.read_text(
                        encoding="utf-8"
                    )
                )
            except (OSError, json.JSONDecodeError):
                return

            self._config = NayeonConfig(
                assistant_name=str(
                    data.get("assistant_name", "Nayeon")
                ),
                user_name=str(
                    data.get("user_name", "Kris")
                ),
                wake_word_enabled=bool(
                    data.get("wake_word_enabled", False)
                ),
                morning_briefing_enabled=bool(
                    data.get("morning_briefing_enabled", True)
                ),
                proactive_enabled=bool(
                    data.get("proactive_enabled", True)
                ),
                settings=dict(
                    data.get("settings", {})
                ),
            )

    def save(self) -> None:
        """Persist configuration to disk."""

        with self._lock:
            self._config_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            data = {
                "assistant_name": self._config.assistant_name,
                "user_name": self._config.user_name,
                "wake_word_enabled": self._config.wake_word_enabled,
                "morning_briefing_enabled": (
                    self._config.morning_briefing_enabled
                ),
                "proactive_enabled": self._config.proactive_enabled,
                "settings": self._config.settings,
            }

            self._config_path.write_text(
                json.dumps(
                    data,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a custom setting."""

        with self._lock:
            return self._config.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a custom setting and persist it."""

        with self._lock:
            self._config.settings[key] = value
            self.save()

    def get_config(self) -> NayeonConfig:
        """Return the current configuration."""

        with self._lock:
            return NayeonConfig(
                assistant_name=self._config.assistant_name,
                user_name=self._config.user_name,
                wake_word_enabled=self._config.wake_word_enabled,
                morning_briefing_enabled=(
                    self._config.morning_briefing_enabled
                ),
                proactive_enabled=self._config.proactive_enabled,
                settings=dict(self._config.settings),
            )