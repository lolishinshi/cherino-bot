from playhouse.db_url import connect

from cherino.config import CONFIG

db = connect(CONFIG.db_url)
