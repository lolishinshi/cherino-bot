from typing import Optional
from pathlib import Path

import tomlkit
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    api_id: Optional[int]
    api_hash: Optional[str]
    token: str
    db_url: str
    nsfw_api: Optional[str] = None


CONFIG = Config(**tomlkit.loads(Path("config.toml").read_text()))
