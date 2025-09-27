from pathlib import Path
import os
import sqlite3
from typing import Iterable, Optional, Tuple


class DB:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def get_cursor(self) -> sqlite3.Cursor:
        if self.conn is None:
            raise DBNotConnected()
        return self.conn.cursor()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        return self

    def disconnect(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        if not self.conn:
            raise DBNotConnected

        cursor = self.conn.cursor()
        return cursor.execute(query, params)

    def executescript(self, query: str) -> sqlite3.Cursor:
        if not self.conn:
            raise DBNotConnected

        return self.conn.executescript(query)

    def executemany(self, query: str, parameters: Iterable) -> sqlite3.Cursor:
        if not self.conn:
            raise DBNotConnected()

        return self.conn.executemany(query, parameters)

    def commit(self):
        if not self.conn:
            raise DBNotConnected

        self.conn.commit()

    def delete_db(self):
        if not self.conn:
            raise DBNotConnected

        self.disconnect()
        os.remove(self.db_path)

    def fetchone(self, query: str, params: Tuple = ()) -> list:
        cursor = self.execute(query, params)
        result = cursor.fetchone()
        if result is None:
            raise QueryNotFound(query)
        return result

    def fetchall(self, query: str, params: Tuple = ()) -> list:
        cursor = self.execute(query, params)
        result = cursor.fetchall()
        if result is None:
            raise QueryNotFound(query)
        return result


class DBNotConnected(Exception):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "Db not connected. Use connect() method before using db"


class QueryNotFound(Exception):
    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__()

    def __str__(self) -> str:
        return f"Query did not achieve a result. Query:\n {self.query}"


class SqliteError(Exception):
    def __init__(self, e: Exception) -> None:
        self.error = e
        super().__init__(e)

    def __str__(self) -> str:
        return f"Sqlite error: {self.error}"
