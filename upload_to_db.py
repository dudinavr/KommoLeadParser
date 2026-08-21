from typing import Any
import asyncio
import uuid
import json
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from db import async_session, MessageRepository, MessageModel, MessageType

JSONS_DIR = Path('chats_njw_fedor') # chats_njw chats_njw_ny chats_njw_fedor


async def upload_messages(
    db_session: AsyncSession, lead_id: int, messages: list[dict[str, Any]]
) -> None:
    repo = MessageRepository(session=db_session)

    await repo.delete_where(MessageModel.lead_id == lead_id)
    chat_id = uuid.uuid4()

    for message in messages:
        if 'SalesBot' in message['author']:
            continue
        msg_type = (
            MessageType.incoming
            if message["direction"] == "incoming"
            else MessageType.outgoing
        )
        msg_created_at = datetime.fromisoformat(message['datetime']) if message['datetime'] else None

        await repo.add(
            MessageModel(
                chat_id=chat_id,
                talk_id=lead_id,
                text=message["text"],
                created_at=msg_created_at,
                lead_id=lead_id,
                type=msg_type,
                client_name=message["client_name"],
                message_origin=message["source"] or 'whatsapp',
            )
        )
    await db_session.commit()


async def main() -> None:

    async with async_session() as db_session:
        for index, json_file in enumerate(sorted(JSONS_DIR.glob("*.json"))):
            messages = json.loads(
                json_file.read_text(encoding="utf-8")
            )
            lead_id = int(json_file.name.split('.json')[0])
            print(f'INDEX: {index} LEAD_ID: {lead_id}')
            print('Lead ID: ', lead_id, 'len: ', len(messages))
            await upload_messages(db_session, lead_id, messages)


asyncio.run(main())
