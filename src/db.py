from typing import Optional
from pathlib import Path
import logging
import json

JSON_DEFAULT_FOLDER = Path.cwd() / "db-hashes"  # Directory for db structure


class Db:
    def __init__(self, db_name: str, create_db: bool = True) -> None:
        """Initiates the db"""
        self.db_name = db_name
        self.db_process = DbProcess(self)

        if create_db:
            self.db_process.create_db()

        try:
            db_data = self.db_process.load()

        except FileNotFoundError as e:
            logging.error(f"No db file found, check if {db_name} exists. {e}")
            return None

        self.db_data = db_data

    @property
    def name(self) -> str:
        return self.db_name

    @property
    def data(self):
        return self.db_data

    def add(self, data: dict | list, key):
        """Adds data to db, use put() method to update the db"""

        if self.db_data.get(key) is None:
            self.db_data.update({key: data})
            return None

        else:
            self.update(data, key)

    def update(self, data: dict | list, key):
        if isinstance(data, list):
            self.db_data[key].extend(data)
        if isinstance(data, dict):
            self.db_data.update({key: data})

    def get(self, key: str):
        return self.db_data.get(key)

    def rm(self, key: str, value: str):
        self.db_data = dict(
            filter(lambda e: e[1].get(key) != value, self.db_data.items())
        )

    def search(self, target, data=None) -> Optional[tuple[str, str]]:
        if data is None:
            data = self.db_data

        for key, value in data.items():
            if isinstance(value, dict):
                result = self.search(target, value)
                if result is not None:
                    return result

            if isinstance(value, list):
                if target in value:
                    return (str(key), str(target))

            if value == target:
                return (str(key), str(value))

        logging.warning("Search did not yield result")
        return None

    def save(self):
        self.db_process.put()

    def load(self):
        self.db_process.load()

    def delete(self):
        self.db_process.delete_db()


class DbProcess:
    def __init__(self, db: Db) -> None:
        self.db_file: Path = JSON_DEFAULT_FOLDER / f"{db.name}.json"
        self.db = db

    def put(self):
        """Sends data to db and updates it"""
        if self.db_file is None:
            logging.error("No db file detected. Use connect() method first")

        try:
            with open(self.db_file, mode="w", encoding="utf-8") as f:
                json.dump(self.db.db_data, f, indent=2)
        except Exception as e:
            logging.error(f"Could not save to json {self.db.db_data}, {e}")

    def load(self):
        with open(self.db_file, mode="r", encoding="utf-8") as f:
            db_data = json.load(f)
            logging.info(f"Loaded db from {self.db.name}")
            return db_data

    def create_db(self) -> None:
        JSON_DEFAULT_FOLDER.mkdir(exist_ok=True)

        file = JSON_DEFAULT_FOLDER / f"{self.db.name}.json"

        if file.exists():
            # logging.warning(f"Db {self.db.name} already exists")
            return None

        try:
            with open(file, mode="w") as f:
                json.dump({}, f)
                logging.info(f"Created db {self.db.name}")

        except Exception as e:
            logging.error(f"Could not create db {self.db.name}, {e}")

    def delete_db(self) -> None:
        file = JSON_DEFAULT_FOLDER / f"{self.db.name}.json"

        file.unlink()

        logging.info(f"Deleted db {self.db.name}")
