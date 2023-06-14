from typing import Optional

from peewee import Case, fn

from cherino.database.models import (
    Answer,
    AnswerHistory,
    PendingVerify,
    Question,
    GroupQuestion,
)


def add_question(
    chat_id: int, description: str, answers: list[str], image: Optional[str] = None
):
    """
    添加一个入群问题
    """
    assert len(answers) > 1
    question = Question.create(
        group=chat_id, description=description, image=image, correct_answer=0
    )
    GroupQuestion.insert(
        group=chat_id, questions=question.group
    ).on_conflict_ignore().execute()

    correct_answer, *other_answers = answers
    for answer in other_answers:
        Answer.insert(question=question, description=answer).execute()
    answer = Answer.create(question=question, description=correct_answer)
    question.correct_answer = answer
    question.save()


def get_all_questions(chat_id: int) -> list[Question]:
    """
    获取所有入群问题
    """
    return list(Question.select().where(Question.group == chat_id))


def get_question_group(chat_id: int) -> list[GroupQuestion]:
    """
    获取问题组
    """
    return list(GroupQuestion.select().where(GroupQuestion.group == chat_id))


def delete_question_group(chat_id: int, question_id: int) -> list[GroupQuestion]:
    """
    删除问题组
    """
    if chat_id == question_id:
        return
    GroupQuestion.delete().where(
        GroupQuestion.group == chat_id, GroupQuestion.id == question_id
    ).execute()


def delete_question(chat_id: int, question_id: int):
    """
    删除一个问题
    """
    question = Question.get_by_id(question_id)
    if question.group != chat_id:
        return
    Answer.delete().where(Answer.question == question_id).execute()
    question.delete_instance()


def get_question(chat_id: int) -> Optional[tuple[Question, Answer]]:
    """
    获取一个入群问题
    """
    try:
        question = (
            Question.select()
            .join(GroupQuestion, on=(Question.group == GroupQuestion.questions))
            .where(GroupQuestion.group == chat_id)
            .order_by(fn.Random())
            .limit(1)
            .get()
        )
        answers = (
            Answer.select().where(Answer.question == question.id).order_by(fn.Random())
        )
    except:
        return None
    return question, answers


def add_answer(user_id: int, chat_id: int, question: int, answer: int) -> bool:
    """
    记录并检查回答是否正确
    """
    AnswerHistory.create(user=user_id, group=chat_id, question=question, answer=answer)
    return (
        Question.select()
        .where(Question.id == question, Question.correct_answer == answer)
        .get_or_none()
    ) is not None


def add_pending_verify(chat_id: int, user_id: int):
    """
    记录待验证用户
    """
    PendingVerify.insert(user=user_id, group=chat_id).on_conflict_replace().execute()


def get_pending_verify(
    chat_id: int, user_id: Optional[int] = None
) -> Optional[PendingVerify] | list[PendingVerify]:
    """
    检查用户是否待验证
    """
    if user_id:
        return (
            PendingVerify.select()
            .where(PendingVerify.user == user_id, PendingVerify.group == chat_id)
            .get_or_none()
        )
    else:
        return list(PendingVerify.select().where(PendingVerify.group == chat_id))


def add_group_question(chat_id: int, group_id: int):
    """
    添加一个来自其他群组的题库
    """
    GroupQuestion.insert(
        group=chat_id, questions=group_id
    ).on_conflict_ignore().execute()


def get_answer_stats(chat_id: int) -> list[tuple[Question, int, int]]:
    """
    查询当前群组题库的回答状态，返回一个列表，每个元素为一个三元组：题目、总回答、正确回答
    """
    query = (
        AnswerHistory.select(
            AnswerHistory.question,
            fn.COUNT(AnswerHistory.question),
            fn.SUM(
                Case(
                    None,
                    ((AnswerHistory.answer == Question.correct_answer, 1),),
                    0,
                )
            ),
        )
        .join(Question, on=(AnswerHistory.question == Question.id))
        .where(Question.group == chat_id)
        .group_by(AnswerHistory.question)
    )
    return [
        (Question.get_by_id(q), total, correct) for q, total, correct in query.tuples()
    ]
