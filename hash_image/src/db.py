from contextlib import ContextDecorator
from dataclasses import dataclass
import psycopg2
from typing import Self
from pathlib import Path

@dataclass
class ModifiedImage:
    id: int
    image_path: Path
    image_id: int
    hasing_method_id: int

@dataclass
class HashMethodIDNotFound(Exception):
    name:str
    def __str__(self) -> str:
        return f"Hashing method {self.name}, not found. Is it in the DB?"

@dataclass
class IDNotReturned(Exception):
    def __str__(self) -> str:
        return "ID not returned from add method"
class Database(ContextDecorator):
    def __init__(self, dbname:str, user:str, password:str, host:str, port:int) -> None:
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)

    def close(self):
        self.conn.close()
    def get_images(self, start: int, fetch_amount: int)->list[ModifiedImage]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM modified_images WHERE id >= %s", (start,))
        result = cur.fetchmany(fetch_amount)

        return [ModifiedImage(id ,p , n, hm) for id, p, n ,hm in result]
    def get_hash_id(self, hash:str, mod_img_id:int, hashing_method:int)->int:

        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM hashes WHERE hash = %s AND modified_image_id = %s AND hashing_method_id = %s", (hash,mod_img_id, hashing_method))
            result = cur.fetchone()
            if result is None:
                raise IDNotReturned()

            return int(result[0])

    def send_hash(self, hash: str, img_id:int, hashing_method_id:int)->int|None:
        command = """
        INSERT INTO hashes (hash, modified_image_id, hashing_method_id) VALUES (%s, %s, %s) 
        ON CONFLICT ON CONSTRAINT unique_image_hash 
        DO NOTHING
        RETURNING id
        """
        with self.conn.cursor() as cur:
            cur.execute(command, (hash, img_id,hashing_method_id))
            result = cur.fetchone()
            if result is None:
                return None

        return int(result[0])

    def get_hash_method_id(self, hash_method_name:str)->int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM hashing_methods WHERE name = (%s)", (hash_method_name,))
        result = cur.fetchone()
        if result is None:
            raise IDNotReturned()

        return int(result[0])

    def add_hash_method(self,hash_method_name:str)->int|None:
        command = """
        INSERT INTO hashing_methods (name) VALUES (%s) 
        ON CONFLICT (name) DO NOTHING
        RETURNING id
        """
        with self.conn.cursor() as cur:
            cur.execute(command, (hash_method_name,))
            result = cur.fetchone()
            if result is None:
                return None

        return int(result[0])
        
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

