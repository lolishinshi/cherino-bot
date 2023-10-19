from peewee import Model, FloatField, BlobField, CharField

from cherino.database import db


class JobStore(Model):
    id = CharField(primary_key=True, max_length=255)
    next_run_time = FloatField(index=True, null=True)
    job_state = BlobField()

    class Meta:
        database = db
