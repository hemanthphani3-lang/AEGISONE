import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("aegisone.email.resend")


class ResendService:
    """Server-only Email Service using the Resend HTTPS API.

    Transports MFA OTP emails over HTTPS without SMTP dependencies.
    Ensures secrets (RESEND_API_KEY, Authorization headers) and OTPs are never logged.
    """

    def __init__(self) -> None:
        self.api_url = "https://api.resend.com/emails"

    def send_email(
        self,
        to_email: str,
        subject: str,
        html: str,
        text: str,
        from_email: str | None = None,
    ) -> tuple[bool, str, str]:
        """Dispatches an email via Resend HTTPS API.

        Returns (success: bool, delivery_status: str, message: str).
        """
        api_key = (os.getenv("RESEND_API_KEY") or "").strip()
        sender = (
            from_email
            or os.getenv("RESEND_FROM_EMAIL")
            or "onboarding@resend.dev"
        ).strip()

        if not api_key:
            logger.warning("Resend API key missing. MFA email delivery is unavailable.")
            return (
                False,
                "UNAVAILABLE",
                "MFA email delivery is currently unavailable. Please contact an administrator.",
            )

        if not sender:
            logger.warning("Resend sender email missing. MFA email delivery is unavailable.")
            return (
                False,
                "UNAVAILABLE",
                "MFA email delivery is currently unavailable. Please contact an administrator.",
            )

        payload: dict[str, Any] = {
            "from": sender,
            "to": [to_email],
            "subject": subject,
            "html": html,
            "text": text,
        }

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.api_url,
                data=data_bytes,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "AegisOne-Backend/0.1.0",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                resp_status = response.getcode()
                if resp_status in (200, 201):
                    logger.info("MFA verification email successfully dispatched via Resend to recipient.")
                    return True, "DELIVERED", f"OTP successfully sent to {to_email}"
                
                logger.error("Resend API returned non-200 status code: %s", resp_status)
                return (
                    False,
                    "ERROR",
                    "MFA email delivery is currently unavailable. Please contact an administrator.",
                )

        except urllib.error.HTTPError as err:
            # Log only safe diagnostic info without exposing headers, keys, or payload secrets
            logger.error("Resend HTTP API Error code %s", err.code)
            return (
                False,
                "ERROR",
                "MFA email delivery is currently unavailable. Please contact an administrator.",
            )
        except urllib.error.URLError as err:
            logger.error("Resend Network connection error")
            return (
                False,
                "ERROR",
                "MFA email delivery is currently unavailable. Please contact an administrator.",
            )
        except Exception:
            logger.error("Unexpected error during Resend email delivery")
            return (
                False,
                "ERROR",
                "MFA email delivery is currently unavailable. Please contact an administrator.",
            )


resend_service = ResendService()
