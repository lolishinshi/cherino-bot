import datetime

from peewee import (
    Model,
    BigIntegerField,
    CharField,
    AutoField,
    TextField,
    DateTimeField,
)

from cherino.database.db import db


class Record(Model):
    id = AutoField()
    # 用户的 Telegram ID
    user = BigIntegerField()
    # 群组 ID
    group = BigIntegerField()
    # 动作
    action = CharField(max_length=15)
    # 原因
    reason = TextField(null=True)
    # 时间
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        indexes = ((("user", "group"), False),)
