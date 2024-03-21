from pathlib import Path

from peewee import Database
from peewee_migrate import Router

from .db import db
from .models import (
    ActionHistory,
    Answer,
    AnswerHistory,
    PendingVerify,
    Question,
    Setting,
    GroupQuestion,
    State,
    JobStore,
    UserLastSeen,
)


def init(db_: Database):
    db_.create_tables(
        [
            Answer,
            Question,
            AnswerHistory,
            ActionHistory,
            PendingVerify,
            Setting,
            GroupQuestion,
            State,
            JobStore,
            UserLastSeen,
        ]
    )
    Router(db_, migrate_dir=Path(__file__).parent / "migrations").run()


init(db)
