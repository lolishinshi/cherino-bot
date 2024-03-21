from peewee import Model, DateTimeField, BigIntegerField, CompositeKey

from cherino.database.db import db


class UserLastSeen(Model):
    id = BigIntegerField()
    chat_id = BigIntegerField()
    last_seen = DateTimeField()
    active_days = BigIntegerField(default=0)

    class Meta:
        database = db
        table_name = "user_last_seen"
        primary_key = CompositeKey("id", "chat_id")
