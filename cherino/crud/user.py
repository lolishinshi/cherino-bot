from datetime import datetime, timedelta
from typing import Optional

from peewee import fn

from cherino.database import ActionHistory, AnswerHistory, UserLastSeen


def warn(user: int, operator: int, group: int, reason: Optional[str] = None) -> int:
    """
    给用户添加一次警告，并返回最近一个月内的警告次数
    """
    ActionHistory.create(
        user=user, operator=operator, group=group, action="warn", reason=reason
    )
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


def ban(user: int, operator: int, group: int, reason: Optional[str] = None):
    """
    封禁用户
    """
    ActionHistory.create(
        user=user, operator=operator, group=group, action="ban", reason=reason
    )


def report(
    user: int, operator: int, group: int, reason: Optional[str] = None
) -> ActionHistory:
    """
    举报用户
    """
    return ActionHistory.create(
        user=user, operator=operator, group=group, action="report", reason=reason
    )


def get_report(report_id: int) -> Optional[ActionHistory]:
    """
    获取举报信息
    """
    return ActionHistory.get_by_id(report_id)


def handle_report(report_id: int, operator: int, action: str) -> Optional[int]:
    """
    处理举报，如果处理结果为警告，则返回处理完后的警告次数
    """
    assert action in ("warn", "ban")
    old_report: ActionHistory = ActionHistory.get_by_id(report_id)
    if action == "ban":
        return ban(
            old_report.user, operator, old_report.group, reason=f"report:{report_id}"
        )
    elif action == "warn":
        return warn(
            old_report.user, operator, old_report.group, reason=f"report:{report_id}"
        )


def max_user_id() -> int:
    """
    获取有记录的最大用户 ID
    """
    return AnswerHistory.select(fn.MAX(AnswerHistory.user)).scalar()


def get_user_last_seen(user: int, chat_id: int) -> Optional[UserLastSeen]:
    """
    获取用户最后一次出现的时间
    """
    return UserLastSeen.get_or_none(id=user, chat_id=chat_id)


def update_user_last_seen(user: int, chat_id: int):
    """
    更新用户最后一次出现的时间，如果与当前时间不在同一天，则活跃天数 +1
    """
    user_last_seen = get_user_last_seen(user, chat_id)
    if user_last_seen is None:
        UserLastSeen.create(id=user, last_seen=datetime.now(), chat_id=chat_id)
    else:
        if user_last_seen.last_seen.date() != datetime.now().date():
            user_last_seen.active_days += 1
        user_last_seen.last_seen = datetime.now()
        user_last_seen.save()
