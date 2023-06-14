from peewee import Model, FloatField, TextField, BlobField

from cherino.database import db


class JobStore(Model):
    id = TextField(primary_key=True)
    next_run_time = FloatField(index=True, null=True)
    job_state = BlobField()

    class Meta:
        database = db
