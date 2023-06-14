from typing import Optional
from pathlib import Path

import tomlkit
from pydantic import BaseSettings


class Config(BaseSettings):
    api_id: Optional[int]
    api_hash: Optional[str]
    token: str
    db_url: str


CONFIG = Config(**tomlkit.loads(Path("config.toml").read_text()))
