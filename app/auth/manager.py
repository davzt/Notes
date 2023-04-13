import uuid

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin, schemas, models, exceptions, FastAPIUsers

from app.auth import auth_backend
from app.config import settings
from app.dependencies import get_user_db
from app.models import UserORM


class UserManager(UUIDIDMixin, BaseUserManager[UserORM, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    # async def on_after_register(
    #     self, user: UserORM, request: Request | None = None
    # ) -> None:
    #     print(f'User {user.username} has registered.')
    #
    # async def on_after_forgot_password(
    #     self, user: UserORM, token: str, request: Request | None = None
    # ) -> None:
    #     print(f'User {user.username} has forgot password. Reset token {token}')
    #
    # async def on_after_request_verify(
    #     self, user: UserORM, token: str, request: Request | None = None
    # ) -> None:
    #     print(f'Verification requested for user {user.username}. Verification token {token}')

    async def create(
            self,
            user_create: schemas.UC,
            safe: bool = False,
            request: Request | None = None,
    ) -> models.UP:
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
            )
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)
        user_dict["notes"] = set()

        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers[UserORM, uuid.UUID](
    get_user_manager,
    [auth_backend],
)
