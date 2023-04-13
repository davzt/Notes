from app.auth.manager import fastapi_users
from app.config import settings

get_current_active_user = fastapi_users.authenticator.current_user(
        active=True, verified=settings.REQUIRES_VERIFICATION
)
get_current_superuser = fastapi_users.authenticator.current_user(
    active=True, verified=settings.REQUIRES_VERIFICATION, superuser=True
)