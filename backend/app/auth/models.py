from pydantic import BaseModel, Field


class AuthenticatedUser(BaseModel):
    """Domain representation of an authenticated user principal."""

    user_id: str
    username: str
    roles: list[str] = Field(default_factory=list)
    mfa_completed: bool = False
    amr: list[str] = Field(default_factory=list)


class AuthMeResponse(BaseModel):
    """Response model for GET /api/v1/auth/me protected endpoint."""

    user_id: str
    username: str
    roles: list[str]
