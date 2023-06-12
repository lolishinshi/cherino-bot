from typing import Optional
from enum import Enum

from cherino.database.models import Setting


class Settings(str, Enum):
    ALLOW_JOIN = "allow_join"
    AUTH_TYPE = "auth_type"
    BAN_TIME = "ban_time"
    ALLOW_NOAUTH_MEDIA = "allow_nonauth_media"


def get_setting(
    chat_id: int, key: Settings, default: Optional[str] = None
) -> Optional[str]:
    """
    获取一个设置
    """
    if setting := Setting.get_or_none(Setting.group == chat_id, Setting.key == key):
        return setting.value
    else:
        return default


def set_setting(chat_id: int, key: Settings, value: str):
    """
    设置一个设置
    """
    Setting.insert(group=chat_id, key=key, value=value).on_conflict_replace().execute()
