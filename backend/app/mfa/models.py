from typing import Optional
from pydantic import BaseModel, Field


class SendOTPRequest(BaseModel):
    """Payload for requesting an Email OTP challenge."""

    email: Optional[str] = Field(None, description="Target email address for OTP delivery")


class SendOTPResponse(BaseModel):
    """Response returned after requesting an OTP delivery."""

    success: bool
    delivery_status: str  # "DELIVERED", "SIMULATED", "UNAVAILABLE", "COOLDOWN"
    cooldown_seconds: int = 60
    message: str


class VerifyOTPRequest(BaseModel):
    """Payload for submitting a 6-digit OTP code."""

    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class VerifyOTPResponse(BaseModel):
    """Response returned after verifying an OTP challenge."""

    success: bool
    mfa_completed: bool = False
    access_token: Optional[str] = None
    token_type: str = "Bearer"
    message: str
