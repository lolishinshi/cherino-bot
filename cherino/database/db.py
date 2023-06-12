import os

from playhouse.db_url import connect

from cherino.config import CONFIG

db = connect(os.getenv("TEST_DB_URL", CONFIG.db_url))
