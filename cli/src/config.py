import os
from pathlib import Path
from dataclasses import dataclass
from typing import Self

# Default values
DEFAULT_MOD_IMG_PATH = Path("/app/modified")
DEFAULT_INPUT_IMG_PATH = Path("/app/input")
DEFAULT_POSTGRESQL_PORT = 5432
DEFAULT_POSTGRESQL_HOST = "db"
DEFAULT_POSTGRESQL_DB = "mydb"
DEFAULT_POSTGRESQL_USER = "user"
DEFAULT_POSTGRESQL_PASSWORD = "password"

@dataclass
class Config:
    orchestrator_url: str

    @classmethod
    def from_env(cls) -> Self:
        return cls(
            orchestrator_url=os.getenv("ORCHESTRATOR_URL","http://localhost:8005"),
        )



