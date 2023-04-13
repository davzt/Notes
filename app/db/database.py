from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from ..config import settings

_engine = create_async_engine(settings.DATABASE_URI, echo=False)
async_session_maker = async_sessionmaker(bind=_engine, expire_on_commit=False)


async def create_async_session() -> AsyncSession:
    return async_session_maker()
