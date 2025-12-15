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
    loader_url: str
    modifier_url: str
    hasher_url: str
    matcher_url: str

    modified_img_path: Path
    input_img_path: Path

    postgresql_port: int
    postgresql_host: str
    postgresql_db: str
    postgresql_user: str
    postgresql_passwd: str

    @classmethod
    def from_env(cls) -> Self:
        return cls(
            loader_url=os.getenv("LOADER_URL", "http://loader:8000"),
            modifier_url=os.getenv("MODIFIER_URL", "http://modifier:8000"),
            hasher_url=os.getenv("HASHER_URL", "http://hasher:8000"),
            matcher_url=os.getenv("MATCHER_URL", "http://matcher:8000"),

            modified_img_path=Path(os.getenv("MOD_IMG_PATH", DEFAULT_MOD_IMG_PATH)),
            input_img_path=Path(os.getenv("INPUT_IMG_PATH", DEFAULT_INPUT_IMG_PATH)),

            postgresql_port=int(os.getenv("POSTGRESQL_PORT", DEFAULT_POSTGRESQL_PORT)),
            postgresql_host=os.getenv("POSTGRESQL_HOST", DEFAULT_POSTGRESQL_HOST),
            postgresql_db=os.getenv("POSTGRESQL_DB", DEFAULT_POSTGRESQL_DB),
            postgresql_user=os.getenv("POSTGRESQL_USER", DEFAULT_POSTGRESQL_USER),
            postgresql_passwd=os.getenv("POSTGRESQL_PASSWORD", DEFAULT_POSTGRESQL_PASSWORD),
        )


