from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.auth.models import AuthMeResponse, AuthenticatedUser

router = APIRouter()


@router.get("/auth/me", response_model=AuthMeResponse)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthMeResponse:
    """Retrieve identity details of the current authenticated user."""
    return AuthMeResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        roles=current_user.roles,
    )
