from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseORM


class UserORM(SQLAlchemyBaseUserTableUUID, BaseORM):
    username: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    notes: Mapped[set["NoteORM"] | None] = relationship(back_populates='user', lazy='selectin', collection_class=set)
# , sa_relationship_kwargs={'lazy': 'selectin'}