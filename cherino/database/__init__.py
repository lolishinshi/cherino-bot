from .db import db
from .models import Answer, Question, ActionHistory, AnswerHistory, PendingVerify

db.create_tables([Answer, Question, AnswerHistory, ActionHistory, PendingVerify])
