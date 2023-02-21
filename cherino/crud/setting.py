from typing import Optional

from cherino.database.models import Setting


def get_setting(chat_id: int, key: str, default: Optional[str] = None) -> Optional[str]:
    """
    获取一个设置
    """
    if setting := Setting.get_or_none(Setting.group == chat_id, Setting.key == key):
        return setting.value
    else:
        return default


def set_setting(chat_id: int, key: str, value: str):
    """
    设置一个设置
    """
    Setting.insert(group=chat_id, key=key, value=value).on_conflict_replace().execute()
