from datetime import datetime, timedelta
from typing import Optional

from cherino.database.models import Record


def warn(user: int, group: int, reason: Optional[str] = None) -> int:
    """
    给用户添加一次警告，并返回最近一个月内的警告次数
    """
    Record.create(user=user, group=group, action="warn", reason=reason)
    cnt = Record.select().where(
        Record.user == user,
        Record.group == group,
        Record.action == "warn",
        Record.created_at > datetime.now() - timedelta(days=30),
    ).count()
    return cnt


def ban(user: int, group: int, reason: Optional[str] = None):
    """
    封禁用户
    """
    Record.create(user=user, group=group, action="ban", reason=reason)
