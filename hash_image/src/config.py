import os
import dataclasses
from typing import Self

DEFAULT_POSTGRESQL_PORT = 5432
DEFAULT_POSTGRESQL_HOST = "localhost"
DEFAULT_POSTGRESQL_DB = "p-hash"
DEFAULT_POSTGRESQL_USER = "user"
DEFAULT_POSTGRESQL_PASSWORD = ""  


@dataclasses.dataclass
class Config:
    postgresql_port: int
    postgresql_host: str
    postgresql_db: str
    postgresql_user: str
    postgresql_passwd: str

    @classmethod
    def from_env(cls) -> Self:

        pg_port_env: str | None = os.getenv("POSTGRESQL_PORT")
        pg_port: int = int(pg_port_env) if pg_port_env else DEFAULT_POSTGRESQL_PORT

        pg_host: str = os.getenv("POSTGRESQL_HOST") or DEFAULT_POSTGRESQL_HOST
        pg_db: str = os.getenv("POSTGRESQL_DB") or DEFAULT_POSTGRESQL_DB
        pg_user: str = os.getenv("POSTGRESQL_USER") or DEFAULT_POSTGRESQL_USER
        pg_pass: str = os.getenv("POSTGRESQL_PASSWORD") or DEFAULT_POSTGRESQL_PASSWORD

        return cls(
            postgresql_port=pg_port,
            postgresql_host=pg_host,
            postgresql_db=pg_db,
            postgresql_user=pg_user,
            postgresql_passwd=pg_pass
        )

