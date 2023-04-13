from fastapi import APIRouter, Depends, Response, status
from fastapi_users import models
from fastapi_users.manager import BaseUserManager

from app.schemas import UserRead, UserUpdate
from app.auth import fastapi_users


def get_user_router(
        requires_verification: bool = False,
) -> APIRouter:

    router = APIRouter(
        prefix='/users',
        tags=['users']
    )

    get_user_manager = fastapi_users.get_user_manager
    authenticator = fastapi_users.authenticator

    get_current_active_user = authenticator.current_user(
        active=True, verified=requires_verification
    )

    @router.delete(
        "/me",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        dependencies=[Depends(get_current_active_user)],
        name="users:delete_current_user",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            }
        },
    )
    async def delete_user(
            user=Depends(get_current_active_user),
            user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        await user_manager.delete(user)
        return None

    router.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
    )

    return router
