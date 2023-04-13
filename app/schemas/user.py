from datetime import datetime
import uuid

from fastapi_users import schemas

from app.schemas.note import Note


class UserBase(schemas.BaseUser[uuid.UUID]):
    username: str


class UserCreate(schemas.BaseUserCreate, UserBase):
    pass


class UserUpdate(schemas.BaseUserUpdate, UserBase):
    username: str | None = None


class UserRead(UserBase):
    created_at: datetime
    notes: list[Note]

    class Config:
        orm_mode = True
