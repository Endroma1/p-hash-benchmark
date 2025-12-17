from contextlib import ContextDecorator
import psycopg2
from typing import  Self
from . import config as cf
from dataclasses import dataclass

class EmptyDatabaseError(Exception):
    def __str__(self) -> str:
        return "The database is empty"

@dataclass
class HashNotFoundError(Exception):
    id:int
    def __str__(self) -> str:
        return f"Did not find hash with id {self.id}"

@dataclass
class Hash:
    id:int
    hash:str
    image_id:int | None= None
    hash_method_id:int | None= None

@dataclass
class HashMethod:
    id:int
    name:str | None = None

@dataclass
class IDNotReturned(Exception):
    def __str__(self) -> str:
        return "ID not returned when attempted to add to db"


class Database(ContextDecorator):
    def __init__(self, dbname:str, user:str, password:str, host:str, port:int) -> None:
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)

        self.max_id:int | None = None


    @classmethod
    def from_config(cls)->Self:
        config = cf.Config.from_env()
        return cls(config.postgresql_db, config.postgresql_user, config.postgresql_passwd, config.postgresql_host, config.postgresql_port)

    def commit(self):
        self.conn.commit()

    def add_hamming_distance(self, hd:float, img_id1:int, img_id2:int)->int|None:
        command = """
        INSERT INTO matches (hamming_distance, hash_id1, hash_id2) 
        VALUES (%s, %s, %s)
        ON CONFLICT ON CONSTRAINT unique_matches DO NOTHING
        RETURNING id
        """
        with self.conn.cursor() as cur:
            cur.execute(command, (hd, img_id1, img_id2))
            result = cur.fetchone()
            if result is None:
                return None

        return int(result[0])

    def get_hash(self, id:int, method_id:int):
        cur = self.conn.cursor()
        command = """
        SELECT h.id, h.hash 
        FROM hashes h
        WHERE h.hashing_method_id = (%s) AND h.id = (%s);
            """
        cur.execute(command, (method_id,id))
        result = cur.fetchone()
        if result is None:
            raise HashNotFoundError(id)

        return Hash(id = result[0], hash = result[1])

    def get_hashes(self, amount:int, start:int, method_id:int):
        cur = self.conn.cursor()
        command = """
        SELECT h.id, h.hash
        FROM hashes h
        WHERE h.hashing_method_id = (%s) AND h.id >= (%s)
        ORDER BY h.id
        LIMIT %s
        """
        cur.execute(command, (method_id, start, amount))
        result = cur.fetchmany(amount)
        return [Hash(id, hash) for id, hash in result]

    def get_hash_methods(self, amount:int, start:int)->list[HashMethod]:
        """
        Gets all hashing methods in batches given by amount
        """
        command = """
        SELECT hm.id 
        FROM hashing_methods hm 
        WHERE hm.id >= (%s)
        ORDER BY id
        LIMIT %s
        """
        cur = self.conn.cursor()
        cur.execute(command, (start,amount))
        result = cur.fetchmany(amount)

        return [HashMethod(id[0]) for id in result]


    def get_max_id(self)->int:
        if self.max_id is not None:
            return self.max_id

        cur = self.conn.cursor()
        cur.execute("SELECTE MAX(id) FROM hashes")
        result = cur.fetchone()

        if result is None:
            raise EmptyDatabaseError()

        return int(result[0])

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
