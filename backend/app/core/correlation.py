import contextvars
import re
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_CORRELATION_ID_REGEX = re.compile(r"^[a-zA-Z0-9\-_]{1,64}$")

correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def validate_correlation_id(val: str | None) -> str | None:
    """Validate correlation ID format to ensure it is bounded and safe."""
    if not val:
        return None
    cleaned = val.strip()
    if _CORRELATION_ID_REGEX.match(cleaned):
        return cleaned
    return None


def get_correlation_id() -> str:
    """Retrieve current correlation ID from contextvar or generate a fallback UUID."""
    cid = correlation_id_var.get()
    if cid:
        return cid
    return str(uuid.uuid4())


def set_correlation_id(cid: str) -> None:
    """Explicitly set correlation ID in current context."""
    correlation_id_var.set(cid)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware for extracting, validating, and propagating correlation IDs."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        header_val = request.headers.get("X-Correlation-ID")
        valid_cid = validate_correlation_id(header_val)

        if not valid_cid:
            valid_cid = str(uuid.uuid4())

        token = correlation_id_var.set(valid_cid)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = valid_cid
            return response
        finally:
            correlation_id_var.reset(token)
