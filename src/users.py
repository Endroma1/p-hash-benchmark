from typing import Optional
from pathlib import Path
from db import Db
from crypt_hash import PathSha256, PilSha256
from PIL import Image
import logging

USERDB = "users"


class User:
    def __init__(self, userid: str, img_names: dict[str, str]) -> None:
        self.userid = userid
        self.img_names = img_names

    def __str__(self) -> str:
        return self.userid

    def __eq__(self, value: object, /) -> bool:
        return self.userid == str(value)

    @property
    def id(self) -> str:
        return self.userid

    @property
    def images(self) -> list[str]:
        return list(self.img_names.keys())

    @classmethod
    def create_user(cls, userid: str, path: Optional[Path] = None) -> Optional["User"]:
        """Creates a user with already known image names or created empty"""
        logging.debug(f"Creating user {userid} from path {path}")

        user = cls(userid, {})

        if path is None:
            return user

        user.add_data(path)

        return user

    @classmethod
    def load_from_db(cls, userid: str, db_name: str = USERDB) -> Optional["User"]:
        db = Db(db_name)

        if db is None:
            return None

        images = db.get(userid)

        if images is None:
            logging.warning(f"User {userid} has no data")
            return None

        return cls(userid, images)

    @classmethod
    def find_user(cls, img_name: str, db_name=USERDB) -> Optional["User"]:
        logging.debug(f"Searching for {img_name} in db {USERDB}")

        db = Db(db_name)

        if db is None:
            return None

        data = db.search(img_name)

        if data is None:
            logging.warning(f"Did not find user for img {img_name}")
            return None

        return cls.load_from_db(data[0])

    def add_data(self, path: Path) -> None:
        if path.is_file():
            hash_str = PathSha256.crypto_hash(path)
            data = {"user": self.userid, "filename": path.name, "hash": str(hash_str)}
            self.img_names.update(data)
            return None

        if not path.is_dir():
            logging.error(f"Path is not a dir or file {path}")
            return None

        paths = list(filter(lambda p: p.is_file(), path.rglob("*")))

        names = map(lambda p: p.name, paths)

        hashes = map(lambda h: str(PathSha256.crypto_hash(h)), paths)

        data = dict(zip(names, hashes))

        self.img_names.update(data)

    def save_to_db(self, db_name: str = USERDB):
        db = Db(db_name)

        if db is None:
            return None

        if db.get(self.userid) is not None:
            print("User already exist, overwrite? y/n")
            choice = input()

            if choice != "y":
                return None

        entries = []
        for name, value in self.img_names.items():
            entry = {"userid": self.userid, "filename": name, "hash": hash}
            entries.append(entry)

        map(db.add, entries)

        db.save()

    def delete_user(self, db_name: str = USERDB):
        print(f"Are you sure you want to delete user {self.userid}? y/n")

        choice = input()

        if choice == "n":
            return None

        db = Db(db_name)

        if db is None:
            return None

        db.rm(self.userid)

    def has_image(self, img_name: str) -> bool:
        return img_name in self.img_names
