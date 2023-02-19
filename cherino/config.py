from pathlib import Path

import tomlkit
from pydantic import BaseSettings


class Config(BaseSettings):
    token: str
    db_url: str


CONFIG = Config(**tomlkit.loads(Path("config.toml").read_text()))