from peewee import (
    AutoField,
    BigIntegerField,
    DeferredForeignKey,
    ForeignKeyField,
    Model,
    TextField,
)

from cherino.database.db import db


class Question(Model):
    id = AutoField()
    # 创建该题目的群组 ID
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


class QuestionGroup(Model):
    id = AutoField()
    # 使用该题库的群组
    group = BigIntegerField(index=True)
    # 题库 ID
    question_group = ForeignKeyField(Question)

    class Meta:
        database = db
        table_name = "question_group"
