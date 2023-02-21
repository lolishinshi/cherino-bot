from .db import db
from .models import (
    ActionHistory,
    Answer,
    AnswerHistory,
    PendingVerify,
    Question,
    Setting,
)

db.create_tables(
    [Answer, Question, AnswerHistory, ActionHistory, PendingVerify, Setting]
)
