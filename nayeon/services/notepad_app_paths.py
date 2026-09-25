"""Resolve only Notepad's independently trusted Windows App Paths registration."""

from dataclasses import replace
import ntpath
from pathlib import Path
import platform

from nayeon.services.application_observation import (
    ApplicationDefinition, DEFAULT_APPLICATIONS, normalize_executable_path,
)


NOTEPAD_APP_PATHS_KEY = r"Software\Microsoft\Windows\CurrentVersion\App Paths\notepad.exe"


def _registry():
    import winreg
    return winreg


def resolve_notepad_definition() -> ApplicationDefinition:
    """Use valid HKCU first, then HKLM, in the process's default registry view.

    No enumeration, PATH resolution, environment expansion, or observation.
    A missing/invalid registration leaves accepted executable identity empty.
    """
    definition = DEFAULT_APPLICATIONS[0]
    if platform.system() != "Windows":
        return definition
    try:
        registry = _registry()
    except (ImportError, OSError):
        return definition
    for hive in (registry.HKEY_CURRENT_USER, registry.HKEY_LOCAL_MACHINE):
        try:
            with registry.OpenKey(hive, NOTEPAD_APP_PATHS_KEY, 0, registry.KEY_READ) as key:
                value, kind = registry.QueryValueEx(key, "")
            if kind != registry.REG_SZ:
                continue
            path = normalize_executable_path(value)
            if ntpath.basename(path) != "notepad.exe" or not Path(path).is_file():
                continue
            return replace(definition, accepted_executable_paths=(path,))
        except (OSError, ValueError, TypeError):
            continue
    return definition
