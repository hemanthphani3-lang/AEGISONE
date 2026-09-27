from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    """Payload for creating a new user account via Keycloak."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    role: str = Field(..., description="AegisOne role: ADMIN, SECURITY_ADMIN, STAFF, STUDENT, BREAK_GLASS")
    password: Optional[str] = Field(None, min_length=8, description="Initial password if set by admin")



class UserResponse(BaseModel):
    """Model representing a user account."""

    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    enabled: bool = True
    roles: list[str] = Field(default_factory=list)
    created_timestamp: Optional[int] = None


class UserToggleRequest(BaseModel):
    """Payload for enabling or disabling a user account."""

    enabled: bool


class UserResetPasswordRequest(BaseModel):
    """Payload for administrative password reset or sending required-action emails."""

    temporary_password: Optional[str] = Field(None, min_length=8)
    send_required_action_email: bool = True
