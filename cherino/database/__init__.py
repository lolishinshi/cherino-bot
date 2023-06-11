from pathlib import Path

from peewee_migrate import Router

from .db import db
from .models import (
    ActionHistory,
    Answer,
    AnswerHistory,
    PendingVerify,
    Question,
    Setting,
    QuestionGroup,
)

db.create_tables(
    [
        Answer,
        Question,
        AnswerHistory,
        ActionHistory,
        PendingVerify,
        Setting,
        QuestionGroup,
    ]
)
Router(db, migrate_dir=Path(__file__).parent / "migrations").run()
