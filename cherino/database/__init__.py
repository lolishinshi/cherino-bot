from .db import db
from .models import Answer, Question, ActionHistory, AnswerHistory

db.create_tables([Answer, Question, AnswerHistory, ActionHistory])
