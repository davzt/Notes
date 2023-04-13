from typing import AsyncGenerator, Annotated

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import create_async_session
from app.models import UserORM


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    db = await create_async_session()
    try:
        yield db
    finally:
        await db.close()


async def get_user_db(session: Annotated[AsyncSession, Depends(get_async_session)]):
    yield SQLAlchemyUserDatabase(session, UserORM)
