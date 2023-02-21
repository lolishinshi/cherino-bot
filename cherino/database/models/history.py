from datetime import datetime

from peewee import (
    Model,
    BigIntegerField,
    CharField,
    AutoField,
    TextField,
    DateTimeField,
    ForeignKeyField,
)

from cherino.database.db import db
from .question import Answer, Question


class ActionHistory(Model):
    id = AutoField()
    # 目标用户的 Telegram ID
    user = BigIntegerField()
    # 发起操作的用户
    operator = BigIntegerField()
    # 群组 ID
    group = BigIntegerField()
    # 动作，可能的值有：warn, ban, report
    action = CharField(max_length=15)
    # 原因
    # 特殊值：report:123，表示处理了 ID 为 123 的举报
    reason = TextField(null=True)
    # 时间
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = "action_history"
        indexes = ((("user", "group"), False),)


class AnswerHistory(Model):
    id = AutoField()
    # 用户的 Telegram ID
    user = BigIntegerField(index=True)
    # 问题 ID
    question = ForeignKeyField(Question, backref="history", index=True)
    # 答案 ID
    answer = ForeignKeyField(Answer)
    # 时间
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = "answer_history"
