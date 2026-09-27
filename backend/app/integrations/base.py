from abc import ABC, abstractmethod
from app.config import ExternalServiceConfig


class AbstractExternalProvider(ABC):
    """Abstract interface for future external service providers.

    Ensures that future integrations obtain credentials exclusively via the central
    ExternalServiceConfig layer rather than directly accessing environment variables or embedding keys.
    """

    def __init__(self, config: ExternalServiceConfig) -> None:
        self.config = config

    @property
    def service_name(self) -> str:
        """Return the name of the external service."""
        return self.config.service_name

    @abstractmethod
    def is_configured(self) -> bool:
        """Verify if credentials and base URL are validly configured."""
        pass
