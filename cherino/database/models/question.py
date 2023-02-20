from datetime import datetime

from peewee import (
    Model,
    TextField,
    BigIntegerField,
    AutoField,
    ForeignKeyField,
    DeferredForeignKey,
    DateTimeField,
)

from cherino.database.db import db


class Question(Model):
    id = AutoField()
    # 群组 ID
    group = BigIntegerField(index=True)
    # 图片 ID（可选）
    image = TextField(null=True)
    # 问题描述
    description = TextField()
    # 正确答案的 ID
    correct_answer = DeferredForeignKey("Answer")

    class Meta:
        database = db


class Answer(Model):
    id = AutoField()
    # 问题 ID
    question = ForeignKeyField(Question, backref="answers", index=True)
    # 答案描述
    description = TextField()

    class Meta:
        database = db


class AnswerHistory(Model):
    id = AutoField()
    # 用户的 Telegram ID
    user = BigIntegerField(index=True)
    # 问题 ID
    question = ForeignKeyField(Question, backref="history", index=True)
    # 答案 ID
    answer = ForeignKeyField(Answer)
    # 时间
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
