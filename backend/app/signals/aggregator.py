from typing import Any
from app.auth.models import AuthenticatedUser
from app.engine.enums import AuthProtocol, UserRole
from app.engine.models import RequestContext
from app.signals.enums import SignalConfidence, SignalSource, SignalStatus
from app.signals.models import SecurityContext, SecuritySignal
from app.signals.provider import AbstractSignalProvider, KeycloakIdentityProvider, LocalContextProvider


class ContextAggregator:
    """Aggregates and normalizes security signals from multiple sources into a SecurityContext."""

    def __init__(self, providers: list[AbstractSignalProvider] | None = None) -> None:
        self.providers = providers if providers is not None else [
            KeycloakIdentityProvider(),
            LocalContextProvider(),
        ]

    def aggregate_sync(
        self,
        principal: AuthenticatedUser | None = None,
        client_data: dict[str, Any] | None = None,
        additional_signals: list[SecuritySignal] | None = None,
    ) -> SecurityContext:
        """Aggregate signals into a deterministic SecurityContext synchronously."""
        context = SecurityContext()

        # 1. Collect signals from configured providers
        if principal:
            keycloak_provider = KeycloakIdentityProvider()
            for sig in keycloak_provider.get_signals_sync(principal):
                context.add_signal(sig)

        if client_data is not None:
            local_provider = LocalContextProvider()
            for sig in local_provider.get_signals_sync(client_data):
                context.add_signal(sig)

        # 2. Add any additional explicitly provided signals
        if additional_signals:
            for sig in additional_signals:
                existing = context.get_signal(sig.name)
                # Conflict resolution: if signal exists, higher confidence or explicit addition overrides
                if not existing or sig.confidence.value >= existing.confidence.value:
                    context.add_signal(sig)

        return context

    async def aggregate_async(
        self,
        principal: AuthenticatedUser | None = None,
        client_data: dict[str, Any] | None = None,
        additional_signals: list[SecuritySignal] | None = None,
    ) -> SecurityContext:
        """Aggregate signals into a deterministic SecurityContext asynchronously."""
        return self.aggregate_sync(principal, client_data, additional_signals)

    @staticmethod
    def from_request_context(req_context: RequestContext) -> SecurityContext:
        """Convert a legacy RequestContext model into a normalized SecurityContext."""
        sec_context = SecurityContext()

        roles = req_context.roles if req_context.roles else ([req_context.role] if req_context.role else [])

        sec_context.add_signal(
            SecuritySignal(
                name="identity.user_id",
                value=req_context.user_id,
                source=SignalSource.LOCAL,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
            )
        )
        sec_context.add_signal(
            SecuritySignal(
                name="identity.roles",
                value=roles,
                source=SignalSource.LOCAL,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
            )
        )
        sec_context.add_signal(
            SecuritySignal(
                name="auth.protocol",
                value=req_context.authentication.protocol,
                source=SignalSource.LOCAL,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
            )
        )
        sec_context.add_signal(
            SecuritySignal(
                name="auth.mfa_completed",
                value=req_context.authentication.mfa_completed,
                source=SignalSource.LOCAL,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.HIGH,
            )
        )
        sec_context.add_signal(
            SecuritySignal(
                name="location",
                value=req_context.location,
                source=SignalSource.LOCAL,
                status=SignalStatus.AVAILABLE,
                confidence=SignalConfidence.MEDIUM,
            )
        )

        dev_managed_status = (
            SignalStatus.AVAILABLE
            if req_context.device.managed is not None
            else SignalStatus.UNKNOWN
        )
        sec_context.add_signal(
            SecuritySignal(
                name="device.managed",
                value=req_context.device.managed,
                source=SignalSource.LOCAL,
                status=dev_managed_status,
                confidence=SignalConfidence.MEDIUM,
            )
        )

        dev_comp_status = (
            SignalStatus.AVAILABLE
            if req_context.device.compliant is not None
            else SignalStatus.UNKNOWN
        )
        sec_context.add_signal(
            SecuritySignal(
                name="device.compliant",
                value=req_context.device.compliant,
                source=SignalSource.LOCAL,
                status=dev_comp_status,
                confidence=SignalConfidence.MEDIUM,
            )
        )

        return sec_context


context_aggregator = ContextAggregator()
