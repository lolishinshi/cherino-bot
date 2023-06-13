from aiogram.fsm.state import StatesGroup, State


class SettingsSG(StatesGroup):
    MAIN = State()
    EDIT_BAN_TIME = State()
    ADD_QUESTION = State()
    EDIT_QUESTION = State()
    DEL_QUESTION = State()
    ADD_QUESTION_GROUP = State()
    DEL_QUESTION_GROUP = State()
    ANSWER_STATS = State()
