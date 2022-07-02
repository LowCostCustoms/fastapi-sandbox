import contextlib
import contextvars
import functools
from typing import Any, Tuple, TypeVar

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy.orm as sao

from api.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL)


class Session(AsyncSession):
    async def get_page(self, query, offset: int, limit: int) -> Tuple[Any, int]:
        paginated_query = query
        if offset is not None:
            paginated_query = paginated_query.offset(offset)

        if limit is not None:
            paginated_query = paginated_query.limit(limit)

        return (
            await self.scalars(paginated_query),
            await self.scalar(sa.select(sa.func.count()).select_from(query.subquery())),
        )


SessionLocal = sao.sessionmaker(autoflush=False, autocommit=False, bind=engine, class_=Session)
FuncT = TypeVar("FuncT")


current_session = contextvars.ContextVar("current_session")


def get_current_session() -> Session:
    return current_session.get()


@contextlib.asynccontextmanager
async def override_session(session: Session):
    token = current_session.set(session)
    try:
        yield
    finally:
        current_session.reset(token)


@contextlib.asynccontextmanager
async def transaction():
    session = get_current_session()
    if session.in_transaction():
        yield
    else:
        await session.begin()
        try:
            yield
            await session.flush()
            await session.commit()
        except:
            await session.rollback()
            raise


def transactional(func: FuncT) -> FuncT:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with transaction():
            return await func(*args, **kwargs)

    return wrapper
