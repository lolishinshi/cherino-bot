from peewee import Model, BigIntegerField, BooleanField, IntegerField, CompositeKey

from cherino.database.db import db


class User(Model):
    # 用户的 Telegram ID
    id = BigIntegerField(primary_key=True)
    # 所属群组
    group = BigIntegerField(index=True)
    # 是否管理员
    is_admin = BooleanField(default=False)

    class Meta:
        database = db
        primary_key = CompositeKey("id", "group")
