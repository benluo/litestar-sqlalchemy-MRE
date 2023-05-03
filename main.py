from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)  # AsyncSession
from litestar.contrib.sqlalchemy.plugins.init import SQLAlchemyAsyncConfig
import uvicorn
from typing import Optional
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import MappedAsDataclass
import pydantic

# from sqlalchemy.engine import result
from litestar import get, post, delete  # put
from litestar.controller import Controller
from litestar.contrib.sqlalchemy.plugins.init import SQLAlchemyInitPlugin
from litestar import Litestar, Router

# from litestar.contrib.sqlalchemy.base import Base as LiteBase

# from litestar.partial import Partial
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


class Base(
    MappedAsDataclass,
    # LiteBase
    DeclarativeBase,
    dataclass_callable=pydantic.dataclasses.dataclass,
):
    pass


class User(Base):
    """User who can use the"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True, init=False
    )  # , autoincrement=True)
    username: Mapped[str]
    password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(insert_default=func.now(), init=False)

    def __repr__(self) -> str:
        """
        Arguments:
        - `self`:
        """
        return self.username


DATABASE_URL = "sqlite+aiosqlite:///db.sqlite"
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_dependency_key="db_session",
)
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class UserController(Controller):
    path = "/users"
    DETAIL_ROUTE = "/{id:int}"

    async def get_item(self, id: int) -> Optional[User]:
        """Get Item by ID."""
        async with async_session() as session:
            return await session.get(User, id)

    @get()
    async def get_users(self) -> list[User]:
        """Get a list of users."""
        # async_session = database.get_session()
        # async_session = async_sessionmaker(database.engine, expire_on_commit=False)
        # rr = []
        async with async_session() as session:
            results = await session.scalars(select(User))
            return [r for r in results]

    @post()
    async def create_user(self, data: User) -> None:
        """Create a `User`."""
        print(data)
        async with async_session() as session:
            session.add(data)
            await session.commit()

    @get(path=DETAIL_ROUTE)
    async def get_user(self, id: int) -> Optional[User]:
        """Get User by ID."""
        async with async_session() as session:
            item = await session.get(User, id)
            return item

    # @put(path=DETAIL_ROUTE)
    # async def update_user(self, data: User, id: int) -> None:
    #     """Update an user."""
    #     pass

    # @patch(path=DETAIL_ROUTE)
    # def partially_update_user(data: Partial[User], id: int) -> None:
    #     """Patch data"""
    #     pass

    @delete(path=DETAIL_ROUTE)  # , status_code=HTTP_200_OK)
    async def delete_user(self, id: int) -> None:
        """Delete User by ID."""
        item = await self.get_item(id)
        if item:
            async with async_session() as session:
                await session.delete(item)
                await session.commit()


router = Router(
    path="/",
    route_handlers=[UserController],
)


# from .controllers import router


async def init_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        admin1 = User(username="admin1", password="admin1")
        admin2 = User(username="admin2", password="admin2")
        user1 = User(username="user1", password="user1")
        user2 = User(username="user2", password="user2")
        session.add_all([admin1, admin2, user1, user2])
        await session.commit()


async def shutdown_database() -> None:
    await engine.dispose()


app = Litestar(
    route_handlers=[
        router,
    ],
    plugins=[
        SQLAlchemyInitPlugin(config=sqlalchemy_config),
    ],
    on_startup=[
        init_database,
    ],
    on_shutdown=[
        shutdown_database,
    ],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8088,
        reload=True,
    )
