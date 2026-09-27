import hashlib
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from typing import Any

from app.email.resend_service import resend_service


class OTPRecord:
    def __init__(self, otp_hash: str, salt: str, expires_at: datetime) -> None:
        self.otp_hash = otp_hash
        self.salt = salt
        self.expires_at = expires_at
        self.attempts = 0
        self.last_sent_at = datetime.now(timezone.utc)


class OTPService:
    """Service managing 6-digit Email OTP generation, hashing, verification, and Resend API delivery."""

    def __init__(
        self,
        ttl_seconds: int = 300,
        cooldown_seconds: int = 60,
        max_attempts: int = 5,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.cooldown_seconds = cooldown_seconds
        self.max_attempts = max_attempts
        self._store: dict[str, OTPRecord] = {}

    def _hash_otp(self, otp: str, salt: str) -> str:
        return hashlib.sha256((salt + otp).encode("utf-8")).hexdigest()

    def generate_otp(self, user_id: str) -> tuple[str, bool, int, str]:
        """Generates a cryptographically random 6-digit OTP code for a user.

        Returns (otp_code, can_send, cooldown_remaining, message).
        """
        now = datetime.now(timezone.utc)
        record = self._store.get(user_id)

        # Check resend cooldown
        if record:
            elapsed = (now - record.last_sent_at).total_seconds()
            if elapsed < self.cooldown_seconds:
                remaining = int(self.cooldown_seconds - elapsed)
                return "", False, remaining, f"Please wait {remaining} seconds before requesting a new OTP."

        # Generate cryptographically secure 6-digit OTP
        code_num = secrets.randbelow(1000000)
        otp_code = f"{code_num:06d}"
        salt = secrets.token_hex(16)
        otp_hash = self._hash_otp(otp_code, salt)
        expires_at = now + timedelta(seconds=self.ttl_seconds)

        # Invalidate previous OTP by replacing record
        self._store[user_id] = OTPRecord(otp_hash=otp_hash, salt=salt, expires_at=expires_at)

        return otp_code, True, 0, "OTP generated successfully."

    def verify_otp(self, user_id: str, otp_code: str) -> tuple[bool, str]:
        """Verifies an OTP code against stored salted hash.

        Returns (is_valid, message).
        """
        now = datetime.now(timezone.utc)
        record = self._store.get(user_id)

        if not record:
            return False, "No active OTP challenge found. Please request a new OTP."

        if now > record.expires_at:
            self._store.pop(user_id, None)
            return False, "OTP has expired. Please request a new OTP."

        if record.attempts >= self.max_attempts:
            self._store.pop(user_id, None)
            return False, "Maximum verification attempts exceeded. Please request a new OTP."

        record.attempts += 1
        input_hash = self._hash_otp(otp_code.strip(), record.salt)

        if secrets.compare_digest(input_hash, record.otp_hash):
            # Verification success: invalidate OTP to prevent reuse
            self._store.pop(user_id, None)
            return True, "OTP verified successfully."

        remaining = self.max_attempts - record.attempts
        return False, f"Invalid OTP code. {remaining} attempt(s) remaining."

    def send_resend_email(self, to_email: str, otp_code: str) -> tuple[bool, str, str]:
        """Delivers 6-digit OTP code to user's email via Resend HTTPS Email API.

        Returns (success, delivery_status, message).
        """
        subject = "AegisOne — Your MFA Verification Code"
        text_content = (
            f"Your AegisOne verification code is:\n\n"
            f"{otp_code}\n\n"
            f"This code expires in 5 minutes.\n\n"
            f"If you did not request this verification code, you can safely ignore this email."
        )
        html_content = (
            f'<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
            f'<body style="font-family: sans-serif; background: #0b0f19; color: #f3f4f6; padding: 20px;">'
            f'<div style="max-width: 480px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 24px;">'
            f'<h2 style="color: #6366f1; margin-top: 0;">AegisOne Security</h2>'
            f'<p>Your AegisOne verification code is:</p>'
            f'<div style="background: #1e1b4b; border: 1px solid #4338ca; border-radius: 6px; padding: 16px; text-align: center; margin: 16px 0;">'
            f'<span style="font-family: monospace; font-size: 28px; font-weight: bold; letter-spacing: 6px; color: #818cf8;">{otp_code}</span>'
            f'</div>'
            f'<p style="color: #9ca3af; font-size: 14px;">This code expires in 5 minutes.</p>'
            f'<p style="color: #6b7280; font-size: 12px; margin-top: 20px; border-top: 1px solid #1f2937; padding-top: 12px;">'
            f'If you did not request this verification code, you can safely ignore this email.</p>'
            f'</div></body></html>'
        )

        return resend_service.send_email(
            to_email=to_email,
            subject=subject,
            html=html_content,
            text=text_content,
        )

    def send_smtp_email(self, to_email: str, otp_code: str) -> tuple[bool, str, str]:
        """Backward-compatibility alias delegating email delivery to Resend HTTPS API."""
        return self.send_resend_email(to_email, otp_code)


otp_service = OTPService()

