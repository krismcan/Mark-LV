"""A-02: strictly test-only fake composition; never production wiring.

Isolation is enforced against rejected inputs and explicitly tested tampering.
A Python interpreter containing arbitrary malicious co-resident code is NOT a
security sandbox: object.__setattr__, monkeypatching and introspection can
defeat pure-Python guards. Do not use this fixture with real credentials.
"""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from threading import RLock

from nayeon.brain.connection_reconciliation import observe_connection
from nayeon.brain.credential_onboarding import OpenAICredentialOnboarding
from nayeon.brain.credential_operation_host import TrustedCredentialOperationHost
from nayeon.brain.onboarding_coordination import CooperativeOnboardingCoordinator
from nayeon.brain.windows_onboarding_mutex import MutexAdmission
from nayeon.secrets.contracts import (
    SecretIdentifier, SecretNotFoundError, SecretValue,
)
from nayeon.secrets.lifecycle import (
    BoundCredentialLifecycle, CredentialValidationStatus,
)


_KEY = SecretIdentifier("openai.api_key")
_LOCK = RLock()
_RESERVED = set()


class FakeBackend:
    __slots__ = ("value", "calls")

    def __init__(self):
        self.value = None
        self.calls = []

    def is_available(self, identifier):
        assert type(identifier) is SecretIdentifier and identifier == _KEY
        self.calls.append("is_available")
        return self.value is not None

    def get(self, identifier):
        assert type(identifier) is SecretIdentifier and identifier == _KEY
        self.calls.append("get")
        if self.value is None:
            raise SecretNotFoundError("Synthetic credential absent")
        return self.value

    def put(self, identifier, value):
        assert type(identifier) is SecretIdentifier and identifier == _KEY
        assert type(value) is SecretValue
        self.calls.append("put")
        self.value = value

    def delete(self, identifier):
        assert type(identifier) is SecretIdentifier and identifier == _KEY
        self.calls.append("delete")
        had_value = self.value is not None
        self.value = None
        return had_value

    def __repr__(self):
        return "FakeBackend(<synthetic>)"


class FakeValidator:
    __slots__ = ("result", "calls")

    def __init__(self, result=CredentialValidationStatus.VALID):
        if type(result) is not CredentialValidationStatus:
            raise TypeError("Exact fake validation result required")
        self.result = result
        self.calls = 0

    def validate(self, value):
        assert type(value) is SecretValue
        self.calls += 1
        return self.result

    def __repr__(self):
        return "FakeValidator(<synthetic>)"


class FakeObserver:
    __slots__ = ("_backend", "_origin_backend", "calls")

    def __init__(self, backend):
        if type(backend) is not FakeBackend:
            raise TypeError("Exact fake backend required")
        object.__setattr__(self, "_backend", backend)
        object.__setattr__(self, "_origin_backend", backend)
        self.calls = 0

    @property
    def backend(self):
        if self._backend is not self._origin_backend:
            raise ValueError("Fake observation identity changed")
        return self._origin_backend

    def __setattr__(self, name, value):
        if name in ("_backend", "_origin_backend") and hasattr(self, name):
            raise AttributeError("Fake observation identity is fixed")
        object.__setattr__(self, name, value)

    def is_available(self, identifier):
        # Direct object.__setattr__ can bypass __setattr__, so check on EACH
        # observation and fail BEFORE calling the replacement backend.
        if self._backend is not self._origin_backend:
            raise ValueError("Fake observation identity changed")
        self.calls += 1
        return self._origin_backend.is_available(identifier)


class FakeMutex:
    __slots__ = ("active", "entries", "exits")

    def __init__(self):
        self.active = False
        self.entries = 0
        self.exits = 0

    @contextmanager
    def hold(self):
        if self.active:
            yield MutexAdmission.BUSY
            return
        self.active = True
        self.entries += 1
        try:
            yield MutexAdmission.HELD
        finally:
            self.active = False
            self.exits += 1


class FakeTempRoot:
    """Test-owned root allocated HERE, not supplied through mutable name text.

    Checks a captured canonical root against the underlying manager on each
    access. Does not claim protection against arbitrary interpreter tampering.
    """
    __slots__ = ("_manager", "_anchor")

    def __init__(self):
        manager = TemporaryDirectory(prefix="nayeon-a02-")
        object.__setattr__(self, "_manager", manager)
        object.__setattr__(self, "_anchor", Path(manager.name).resolve())

    @property
    def path(self):
        root = self._anchor
        if (Path(self._manager.name).resolve() != root or
                Path(self._manager.name) != root or
                not root.is_dir() or root.is_symlink()):
            raise ValueError("Test temporary-directory ownership changed")
        return root

    def __setattr__(self, name, value):
        raise AttributeError("Fake temporary-root owner is read-only")

    def cleanup(self):
        self._manager.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.cleanup()


class FakeComposition:
    __slots__ = ("host", "coordinator", "controller", "backend", "validator",
                 "observer", "mutex", "metadata_path")

    def __init__(self, host, coordinator, backend, validator, observer, mutex,
                 metadata_path):
        for key, value in (
            ("host", host), ("coordinator", coordinator),
            ("controller", coordinator.recovery_controller),
            ("backend", backend), ("validator", validator),
            ("observer", observer), ("mutex", mutex),
            ("metadata_path", metadata_path),
        ):
            object.__setattr__(self, key, value)

    def __setattr__(self, name, value):
        raise AttributeError("Fake composition references are read-only")

    def __repr__(self):
        return "FakeComposition(<synthetic-only>)"


def _fixed_fake_factory(
    backend_type=FakeBackend, validator_type=FakeValidator,
    observer_type=FakeObserver, mutex_type=FakeMutex,
    root_type=FakeTempRoot, path_type=type(Path()),
):
    # Captured class identities cannot be redirected simply by rebinding
    # module globals. Capture relevant class descriptors before user input.
    trusted_methods = tuple(
        (cls, name, cls.__dict__[name])
        for cls, names in (
            (backend_type, ("__init__", "is_available", "get", "put", "delete")),
            (validator_type, ("__init__", "validate")),
            (observer_type, ("__init__", "backend", "is_available", "__setattr__")),
            (mutex_type, ("__init__", "hold")),
            (root_type, ("__init__", "path", "__setattr__")),
        )
        for name in names
    )

    def compose_fake_only_onboarding(*, backend, validator, observer, mutex,
                                     temp_root, metadata_path):
        """Reject modified dependencies before attribute inspection or effects.

        A deterministic test-only factory, not a privilege boundary for code
        executing arbitrary Python in the same interpreter.
        """
        if (type(backend) is not backend_type or
                type(validator) is not validator_type or
                type(observer) is not observer_type or
                type(mutex) is not mutex_type or
                type(temp_root) is not root_type or
                type(metadata_path) is not path_type):
            raise TypeError("Exact A-02 fake dependencies and native path required")
        if any(cls.__dict__.get(name) is not original
               for cls, name, original in trusted_methods):
            raise TypeError("Fake dependency class definition changed")
        if observer.backend is not backend:
            raise ValueError("Fake observer/backend identity mismatch")
        root = temp_root.path  # Verified captured owner; no caller-chosen name.
        trusted_temp = Path(gettempdir()).resolve()
        if (not root.is_relative_to(trusted_temp) or root == trusted_temp or
                root.parent != trusted_temp or
                metadata_path.parent != root or
                metadata_path.name != "provider.json" or
                metadata_path != metadata_path.resolve() or
                metadata_path.exists()):  # Includes existing regular files.
            raise ValueError("Metadata must be fresh, canonical and test-owned")
        key = str(metadata_path).casefold()
        with _LOCK:
            if key in _RESERVED:
                raise ValueError("Duplicate test-only composition path")
            lifecycle = BoundCredentialLifecycle(backend, _KEY, validator)
            onboarding = OpenAICredentialOnboarding(lifecycle)
            host = TrustedCredentialOperationHost(
                onboarding=onboarding,
                observe=lambda: observe_connection(metadata_path, observer),
            )
            coordinator = CooperativeOnboardingCoordinator(
                host=host, metadata_path=metadata_path, availability=observer,
                mutex=mutex,
            )
            result = FakeComposition(host, coordinator, backend, validator,
                                     observer, mutex, metadata_path)
            _RESERVED.add(key)
            return result
    return compose_fake_only_onboarding


compose_fake_only_onboarding = _fixed_fake_factory()
del _fixed_fake_factory
