import uuid

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from typing import Annotated
from enum import Enum

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DB_URL = ''

engine = create_async_engine(
    DB_URL,
    echo=True,
)

async_session = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)

CreatedAtColumn = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    ),
]


class Base(DeclarativeBase):
    pass


class MessageType(Enum):
    incoming = "incoming"
    outgoing = "outgoing"


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[uuid.UUID]
    talk_id: Mapped[int]
    text: Mapped[str]
    created_at: Mapped[CreatedAtColumn]
    lead_id: Mapped[int]
    type: Mapped[MessageType]
    client_name: Mapped[str]
    message_origin: Mapped[str]
    attachment_link: Mapped[str | None]

class MessageRepository(SQLAlchemyAsyncRepository[MessageModel]):
    model_type = MessageModel

