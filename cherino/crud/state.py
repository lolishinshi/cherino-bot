import json
from typing import Any, Dict, Optional, Literal

from aiogram import Bot
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

from cherino.database.models.state import State


def build_key(key: StorageKey, part: Literal["data", "state"]):
    return f"{key.chat_id}:{key.user_id}:{key.destiny}:{part}"


class SqliteStorage(BaseStorage):
    async def set_state(
        self, bot: Bot, key: StorageKey, state: StateType = None
    ) -> None:
        key = build_key(key, "state")
        State.insert(key=key, value=state.state if isinstance(state, State) else state).on_conflict_replace().execute()

    async def get_state(self, bot: Bot, key: StorageKey) -> Optional[str]:
        key = build_key(key, "state")
        if state := State.get_or_none(State.key == key):
            return state.value
        else:
            return None

    async def set_data(self, bot: Bot, key: StorageKey, data: Dict[str, Any]) -> None:
        key = build_key(key, "data")
        if not data:
            State.delete().where(State.key == key).execute()
            return
        State.insert(key=key, value=json.dumps(data)).on_conflict_replace().execute()

    async def get_data(self, bot: Bot, key: StorageKey) -> Dict[str, Any]:
        key = build_key(key, "data")
        if state := State.get_or_none(State.key == key):
            return json.loads(state.value)
        else:
            return {}

    async def close(self) -> None:
        pass
