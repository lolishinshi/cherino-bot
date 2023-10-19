from peewee import Model, TextField, CharField

from cherino.database import db


class State(Model):
    key = CharField(primary_key=True, max_length=255)
    value = TextField()

    class Meta:
        database = db
