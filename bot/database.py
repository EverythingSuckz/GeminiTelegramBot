import logging
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

import databases
import ormar
import sqlalchemy
from google.generativeai import ChatSession

from config import Config

logger = logging.getLogger(__name__)

base_ormar_config = ormar.OrmarConfig(
    database=databases.Database(Config.DATABASE_URI),
    metadata=sqlalchemy.MetaData(),
    engine=sqlalchemy.create_engine(Config.DATABASE_URI),
)

class Role(str, Enum):
    USER = ChatSession._USER_ROLE
    MODEL = ChatSession._MODEL_ROLE

class User(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="user",
    )
    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=255)
    username = ormar.String(max_length=255, nullable=True)
    started_at = ormar.DateTime(default=lambda: datetime.now(timezone.utc))


class File(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="file",
    )
    id = ormar.Integer(primary_key=True, autoincrement=True)
    mime_type = ormar.String(max_length=255)
    url = ormar.String(max_length=255)


class Part(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="part",
    )
    id = ormar.Integer(primary_key=True, autoincrement=True)
    text = ormar.Text(nullable=True)
    file = ormar.ForeignKey(File, nullable=True)


class History(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="history",
    )
    id = ormar.Integer(primary_key=True, autoincrement=True)
    chat_id = ormar.Integer()
    role: Enum = ormar.Enum(enum_class=Role)
    parts: List[Part] = ormar.ManyToMany(Part)


class DatabaseWrapper:
    def __init__(self):
        self.is_init = False
        
    async def setup_database(self):
        logger.info("Setting up database...")
        await base_ormar_config.database.connect()
        base_ormar_config.metadata.create_all(base_ormar_config.engine)
        logger.info("Database setup successful.")
        self.is_init = True
    
    async def get_user(self, id: int) -> Optional[User]:
        return await User.objects.get_or_none(id=id)
    
    async def aou_user(self, id: int, name: str, username: Optional[str], **kwargs)  -> bool:
        """
        Adds or updates a user.
        returns `True` if user is added, False if user is updated.
        TODO: Welcome the user if the the user is starting the bot for the first time.
        """
        user = await self.get_user(id)
        if user:
            kwargs.pop("started_at", None)
            await User.objects.filter(id=id).update(username=username, **kwargs)
            return False
        else:
            await User.objects.create(id=id, name=name, username=username, **kwargs)
            return True
    
    async def set_user_history(
        self,
        user_id: int,
        message: Optional[str] = None,
        mime_type: Optional[str] = None,
        url: Optional[str] = None,
        ):
        """
        Set user history.
        """
        parts = []
        if message:
            parts.append(await Part.objects.create(text=message.strip()))
        if mime_type and url:
            parts.append(await Part.objects.create(file=await File.objects.create(mime_type=mime_type, url=url)))
        
        history = await History.objects.create(
            chat_id=user_id,
            role=Role.USER
        )
        
        for part in parts:
            await history.parts.add(part)

    async def set_response_history(self, user_id: int, message: str):
        """
        Set response history.
        """
        part = await Part.objects.create(text=message.strip())
        history = await History.objects.create(
            chat_id=user_id,
            role=Role.MODEL,
        )
        await history.parts.add(part)
        
        
    async def get_one_history(self, user_id: int) -> Optional[History]:
        """
        Get one history of a user.
        """
        return await History.objects.filter(chat_id=user_id).select_related("parts").order_by("-id").first()

    async def get_history(self, user_id: int) -> List[History]:
        """
        Get history of a user.
        """
        
        return list(
                    await History.objects.filter(chat_id=user_id)
                    .select_related(["parts", "parts__file"])
                    .order_by("id")
                    .limit(50)
                    .all()
                )

    async def clear_history(self, user_id: int):
        """
        Clears the history of a user.
        """
        await History.objects.filter(chat_id=user_id).delete()
