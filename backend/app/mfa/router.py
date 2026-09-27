from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser
from app.config import JWT_SECRET_KEY
from app.mfa.models import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.mfa.service import otp_service

router = APIRouter(prefix="/auth/mfa", tags=["MFA"])


def create_mfa_upgraded_token(user: AuthenticatedUser) -> str:
    """Create a new JWT token containing amr=['otp'] and mfa_completed=True claim."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user.user_id,
        "preferred_username": user.username,
        "roles": user.roles,
        "realm_access": {"roles": user.roles},
        "amr": ["otp"],
        "acr": "2",
        "mfa_completed": True,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=8)).timestamp()),
        "iss": "http://localhost:8080/realms/accessguard",
        "aud": "accessguard-backend",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp_challenge(
    payload: SendOTPRequest = SendOTPRequest(),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SendOTPResponse:
    """Generate and dispatch a 6-digit Email OTP to the authenticated user's email."""
    otp_code, can_send, cooldown_remaining, msg = otp_service.generate_otp(current_user.user_id)
    if not can_send:
        return SendOTPResponse(
            success=False,
            delivery_status="COOLDOWN",
            cooldown_seconds=cooldown_remaining,
            message=msg,
        )

    target_email = payload.email or f"{current_user.username}@aegisone.local"
    success, delivery_status, delivery_msg = otp_service.send_resend_email(target_email, otp_code)

    if not success and delivery_status == "UNAVAILABLE":
        # System configured without Resend API key -> Return clear notification but allow dev simulation
        return SendOTPResponse(
            success=True,
            delivery_status="SIMULATED",
            cooldown_seconds=60,
            message="Resend API key is not configured. OTP generated for dev verification (check backend telemetry).",
        )

    return SendOTPResponse(
        success=success,
        delivery_status=delivery_status,
        cooldown_seconds=60,
        message=delivery_msg,
    )


@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp_challenge(
    payload: VerifyOTPRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> VerifyOTPResponse:
    """Verify a 6-digit OTP code and issue an upgraded JWT session token with auth.mfa_completed=True."""
    is_valid, msg = otp_service.verify_otp(current_user.user_id, payload.otp_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    # Issue upgraded token with mfa_completed = true
    upgraded_token = create_mfa_upgraded_token(current_user)

    return VerifyOTPResponse(
        success=True,
        mfa_completed=True,
        access_token=upgraded_token,
        message="OTP challenge verified successfully. MFA completion recorded.",
    )
