from typing import Optional

from peewee import fn

from cherino.database.models import Question, Answer, AnswerHistory, PendingVerify


def add_question(
    chat_id: int, description: str, answers: list[str], image: Optional[str] = None
):
    """
    添加一个入群问题
    """
    question = Question.create(
        group=chat_id, description=description, image=image, correct_answer=0
    )
    correct_answer, *other_answers = answers
    for answer in other_answers:
        Answer.insert(question=question, description=answer).execute()
    answer = Answer.create(question=question, description=correct_answer)
    question.correct_answer = answer
    question.save()


def get_question(chat_id: int) -> Optional[tuple[Question, Answer]]:
    """
    获取一个入群问题
    """
    try:
        question = (
            Question.select()
            .where(Question.group == chat_id)
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


def add_answer(user_id: int, question: int, answer: int) -> bool:
    """
    记录并检查回答是否正确
    """
    AnswerHistory.create(user=user_id, question=question, answer=answer)
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
