from contextlib import ContextDecorator
from dataclasses import dataclass
import psycopg2
from typing import Generator, Self
from pathlib import Path

@dataclass
class ModificationIDNotFound(Exception):
    name:str
    def __str__(self) -> str:
        return f"Could not find id for modification {self.name}. Is it in the DB?"

@dataclass
class IDNotReturned(Exception):
    def __str__(self) -> str:
        return f"Adding did not return ID"

@dataclass
class Image:
    id: int
    path: Path
    user_id: int

class Database(ContextDecorator):
    def __init__(self, dbname:str, user:str, password:str, host:str, port:int) -> None:
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)

    def close(self):
        self.conn.close()

    def get_images(self, start: int, fetch_amount: int)->Generator[Image]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, path, user_id FROM images WHERE id >= %s", (start,))
        results = cur.fetchmany(fetch_amount)

        for id, path ,uid in results:
            yield Image(id, Path(path), uid)

    def get_user_id(self, name: str)->int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM users WHERE name = (%s)", (name,))
        result = cur.fetchone()
        if result is not None:
            return int(result[0])
        else:
            raise ValueError(f"Could not find user {name}")

    def add_mod_image(self, path:Path, image_id:int, mod_id:int)->int:
        command = """
        INSERT INTO modified_images (path, image_id, modification_id) VALUES (%s, %s, %s) 
        ON CONFLICT (path) DO NOTHING;
        DO UPDATE SET path = EXCLUDED.path
        RETURNING id
        """
        with self.conn.cursor() as cur:
            cur.execute(command, (str(path),image_id, mod_id))
            result = cur.fetchone()

            if result is None:
                raise IDNotReturned()

        return int(result[0])

    def get_mod_id(self, mod_name:str)->int|None:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM modifications WHERE name = (%s)", (mod_name,))
        result = cur.fetchone()

        if result is None:
            return None

        return result[0]

    def add_modification(self, mod_name:str)->int:
        command = """
        INSERT INTO modifications (name) (%s) 
        ON CONFLICT (name) DO NOTHING;
        DO UPDATE SET path = EXCLUDED.path
        RETURNING id
        """
        with self.conn.cursor() as cur:
            cur.execute(command, (mod_name,))
            result = cur.fetchone()
            
            if result is None:
                raise IDNotReturned()

        return int(result[0])

    def commit(self):
        """
        Manual commit if neede. Usually if adding doing lot of stuff on one connection
        """
        self.conn.commit()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
