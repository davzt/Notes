from fastapi import FastAPI

from app.auth import auth_backend
from app.routers import get_user_router, get_note_router
from app.schemas import UserRead, UserCreate
from app.auth import fastapi_users

app = FastAPI(
    title="Notes App"
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
        get_user_router()
    )

app.include_router(
        get_note_router()
    )
