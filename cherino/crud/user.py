from datetime import datetime, timedelta
from typing import Optional

from cherino.database.models import ActionHistory


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
