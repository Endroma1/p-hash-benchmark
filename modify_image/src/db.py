from contextlib import ContextDecorator
from dataclasses import dataclass
import psycopg2
from typing import Self
from pathlib import Path

@dataclass
class ModificationIDNotFound(Exception):
    name:str
    def __str__(self) -> str:
        return f"Could not find id for modification {self.name}. Is it in the DB?"

class Database(ContextDecorator):
    def __init__(self, dbname:str, user:str, password:str, host:str, port:int) -> None:
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)

    def add_image(self, path:Path, name:str, mod_name:str):
        mod_id:int = self.get_mod_id(mod_name)
        command = """
        INSERT INTO images (path, name, modification_id) VALUES (%s, %s, %s) 
        ON CONFLICT (path) DO NOTHING;
            """
        cur = self.conn.cursor()
        cur.execute(command, (str(path), name, mod_id))
        cur.close()

    def get_mod_id(self, mod_name:str)->int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM modifications WHERE name = (%s)", (mod_name,))
        result = cur.fetchone()

        if result is None:
            raise ModificationIDNotFound(mod_name)

        return result[0]

    def add_modification(self, mod_name:str):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO modifications (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;",(mod_name,))

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
