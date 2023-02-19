from playhouse.db_url import connect

from cherino.config import CONFIG
from .models import Answer, Question, User

db = connect(CONFIG.db_url)
db.create_tables([Answer, Question, User])
