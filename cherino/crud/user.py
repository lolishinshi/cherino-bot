from datetime import datetime, timedelta
from typing import Optional

from cherino.database.models import ActionHistory


def warn(user: int, group: int, reason: Optional[str] = None) -> int:
    """
    给用户添加一次警告，并返回最近一个月内的警告次数
    """
    ActionHistory.create(user=user, group=group, action="warn", reason=reason)
    cnt = (
        ActionHistory.select()
        .where(
            ActionHistory.user == user,
            ActionHistory.group == group,
            ActionHistory.action == "warn",
            ActionHistory.created_at > datetime.now() - timedelta(days=30),
        )
        .count()
    )
    return cnt


def ban(user: int, group: int, reason: Optional[str] = None):
    """
    封禁用户
    """
    ActionHistory.create(user=user, group=group, action="ban", reason=reason)
