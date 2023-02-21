from datetime import datetime

from peewee import BigIntegerField, CompositeKey, DateTimeField, Model

from cherino.database.db import db


class PendingVerify(Model):
    user = BigIntegerField()
    group = BigIntegerField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = "pending_verify"
        primary_key = CompositeKey("user", "group")
