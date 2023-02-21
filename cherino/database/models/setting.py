from peewee import BigIntegerField, CharField, CompositeKey, Model, TextField

from cherino.database.db import db


class Setting(Model):
    group = BigIntegerField()
    key = CharField(max_length=16)
    value = TextField()

    class Meta:
        database = db
        primary_key = CompositeKey("group", "key")
