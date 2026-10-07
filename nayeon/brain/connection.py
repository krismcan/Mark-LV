"""Non-secret provider metadata; no resolution or management authority."""

from dataclasses import dataclass

from nayeon.secrets.contracts import SecretIdentifier


@dataclass(frozen=True, slots=True)
class ProviderConnectionConfiguration:
    """Metadata only; trusted composition must bind provider credential identity.

    No provider-to-credential mapping is enforced by this contract.
    """

    provider: str
    model: str
    credential: SecretIdentifier

    def __post_init__(self) -> None:
        if type(self.provider) is not str:
            raise TypeError("Provider must be an exact str")
        if not 1 <= len(self.provider) <= 64:
            raise ValueError("Invalid provider length")
        initial = "abcdefghijklmnopqrstuvwxyz0123456789"
        if self.provider[0] not in initial or any(
            character not in initial + "._-" for character in self.provider[1:]
        ):
            raise ValueError("Invalid provider syntax")
        if type(self.model) is not str:
            raise TypeError("Model must be an exact str")
        if not 1 <= len(self.model) <= 128:
            raise ValueError("Invalid model length")
        if self.model != self.model.strip() or not self.model.isprintable():
            raise ValueError("Invalid model text")
        if type(self.credential) is not SecretIdentifier:
            raise TypeError("Credential must be an exact SecretIdentifier")
