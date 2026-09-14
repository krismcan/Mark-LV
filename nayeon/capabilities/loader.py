"""Automatic discovery of self-describing Nayeon capabilities."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType

from nayeon.registry import CapabilityRegistry

from .base import CapabilityModule


class CapabilityLoader:
    """Discover and register capability modules."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def discover(self, package_name: str = "nayeon.capabilities") -> int:
        """Discover capability modules and register their metadata.

        Returns the number of newly discovered capabilities.
        """

        package = importlib.import_module(package_name)
        discovered = 0

        for module_info in pkgutil.iter_modules(package.__path__):
            module_name = module_info.name

            # Internal framework modules are not capabilities.
            if module_name.startswith("_") or module_name in {
                "base",
                "loader",
            }:
                continue

            full_name = f"{package_name}.{module_name}"

            try:
                module = importlib.import_module(full_name)
            except Exception:
                continue

            discovered += self._load_module(module)

        return discovered

    def _load_module(self, module: ModuleType) -> int:
        """Find and register capability implementations in one module."""

        count = 0

        for _, cls in inspect.getmembers(
            module,
            inspect.isclass,
        ):
            if not issubclass(cls, CapabilityModule):
                continue

            if cls is CapabilityModule:
                continue

            if inspect.isabstract(cls):
                continue

            try:
                instance = cls()
                capability = instance.capability
            except Exception:
                continue

            try:
                self._registry.register(capability)
            except ValueError:
                # Duplicate registrations are ignored during discovery.
                continue

            count += 1

        return count