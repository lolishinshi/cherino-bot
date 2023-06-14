from peewee import Model, TextField

from cherino.database import db


class State(Model):
    key = TextField(primary_key=True)
    value = TextField()

    class Meta:
        database = db
