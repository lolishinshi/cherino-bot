from cherino.crud import auth
from cherino.database import db, init


def init_db():
    db.init(database=":memory:")
    # db.bind([auth.Question, auth.GroupQuestion])
    init(db)
    auth.add_question(1, "question1", ["test1", "test2", "test3"])
    auth.add_question(1, "question2", ["test1", "test2", "test3"])
    auth.add_question(2, "question3", ["test1", "test2", "test3"])
    auth.add_question(2, "question4", ["test1", "test2", "test3"])


class TestAuth:
    def test_question(self):
        init_db()
        assert len(auth.get_all_questions(1)), 4
