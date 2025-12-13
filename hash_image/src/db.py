from contextlib import ContextDecorator
from dataclasses import dataclass
import psycopg2
from typing import Self
from pathlib import Path

@dataclass
class Image:
    id: int
    image_path: Path
    name: str
    hasing_method_id: int

@dataclass
class HashMethodIDNotFound(Exception):
    name:str
    def __str__(self) -> str:
        return f"Hashing method {self.name}, not found. Is it in the DB?"

class Database(ContextDecorator):
    def __init__(self, dbname:str, user:str, password:str, host:str, port:int) -> None:
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)

    def get_images(self, start: int, fetch_amount: int)->list[Image]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM images WHERE id >= %s", (start,))
        result = cur.fetchmany(fetch_amount)

        return [Image(id ,p , n, hm) for id, p, n ,hm in result]

    def send_hash(self, hash: str, img_id:int, hashing_method_name:str):
        hash_method_id = self.get_hash_method_id(hashing_method_name)
        cur = self.conn.cursor()
        cur.execute("INSERT INTO hashes (hash, image_id, hashing_method_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (hash, img_id,hash_method_id))

    def get_hash_method_id(self, hash_method_name:str)->int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM hashing_methods WHERE name = (%s)", (hash_method_name,))
        result = cur.fetchone()
        if result is None:
            raise HashMethodIDNotFound(hash_method_name)

        return int(result[0])

    def add_hash_method(self,hash_method_name:str)->Self:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO hashing_methods (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (hash_method_name,))
        return self
        
    def commit(self):
        self.conn.commit()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()

