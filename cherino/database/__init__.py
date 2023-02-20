from .db import db
from .models import Answer, Question, Record, AnswerHistory

db.create_tables([Answer, Question, AnswerHistory, Record])
