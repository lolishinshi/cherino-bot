import json
from typing import Any
from enum import StrEnum

from cherino.database.models import Setting


class Settings(StrEnum):
    ALLOW_JOIN = "allow_join"
    AUTH_IN_GROUP = "auth_in_group"
    BAN_TIME = "ban_time"
    ALLOW_NOAUTH_MEDIA = "allow_nonauth_media"
    GREAT_PURGE = "great_purge"  # 废弃
    CHECK_PORN = "check_porn"
    AGGRESSIVE_ANTISPAM = "aggressive_antispam"


DEFAULT_VALUE = {
    Settings.ALLOW_JOIN: True,
    Settings.AUTH_IN_GROUP: True,
    Settings.BAN_TIME: "1h",
    Settings.ALLOW_NOAUTH_MEDIA: False,
    Settings.CHECK_PORN: False,
    Settings.AGGRESSIVE_ANTISPAM: False,
}


def get_setting(chat_id: int, key: Settings) -> Any:
    """
    获取一个设置
    """
    if setting := Setting.get_or_none(Setting.group == chat_id, Setting.key == key):
        return json.loads(setting.value)
    else:
        return DEFAULT_VALUE[key]


def set_setting(chat_id: int, key: Settings, value: Any):
    """
    设置一个设置
    """
    value = json.dumps(value)
    Setting.insert(group=chat_id, key=key, value=value).on_conflict_replace().execute()
