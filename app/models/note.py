from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Sequence
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseORM


class NoteORM(BaseORM):
    notes_seq = Sequence('notes_id_seq', start=1)
    user_id: Mapped[UUID] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    note_id: Mapped[int] = mapped_column(notes_seq, primary_key=True, index=True, server_default=notes_seq.next_value())
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_time_limited: Mapped[bool] = mapped_column(default=False)
    time_limit: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())

    user: Mapped["UserORM"] = relationship(back_populates='notes', lazy='selectin')
