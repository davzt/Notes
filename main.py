from fastapi import FastAPI, Depends

from app.auth import auth_backend
from app.models import UserORM
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

current_user = fastapi_users.current_user()


@app.get("/protected-route")
def protected_route(user: UserORM = Depends(current_user)):
    return f"Hello, {user.username}"


@app.get("/unprotected-route")
def unprotected_route():
    return f"Hello, anonym"
