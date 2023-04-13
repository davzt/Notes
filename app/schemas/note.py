from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NoteBase(BaseModel):
    title: str
    description: str | None = None
    is_time_limited: bool = False
    time_limit: datetime | None = None

    class Config:
        orm_mode = True


class NoteCreate(NoteBase):
    # user_id: UUID
    pass


class NoteUpdate(NoteBase):
    title: str | None
    is_time_limited: bool | None
    is_active: bool | None

    class Config:
        orm_mode = True


class Note(NoteBase):
    user_id: UUID
    note_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    class Config:
        orm_mode = True
