import logging
from db import Db
from typing import Optional
from PIL import Image
from users import User
from pathlib import Path
from hash_methods import AverageHash
from interfaces import HashMethod
from rich import print


class ImageHash:
    def __init__(
        self,
        hash: str,
        method_name: str,
        img_path: Optional[Path] = None,
        img_name: Optional[str] = None,
    ) -> None:
        self._hash = hash
        if img_path is not None:
            self._name = img_path.name
        elif img_name is not None:
            self._name = img_name
        else:
            raise ValueError("img_path or img_name not given to ImageHash constructor")
        self._method = method_name

    @property
    def length(self) -> int:
        return len(self._hash)

    @property
    def method(self) -> str:
        return self._method

    @property
    def name(self) -> str:
        return self._name

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def as_bin(self) -> str:
        num = int(self._hash, 16)
        binary = bin(num)
        no_prefix = binary[2:]
        return no_prefix

    def user(self) -> Optional[User]:
        """Returns the user that owns the hashed image"""
        return User.find_user(self._name)

    def save_to_db(self):
        entry = [{"hash": self._hash, "name": self._name, "method": self._method}]

        db = Db(f"hashes_{self._method}")
        user = self.user()

        if user is None:
            logging.warning(f"Did not find user for image {self._name}")
            return None

        db.add(entry, user.id)
        db.save()

    @classmethod
    def load_all_hashes_from_db(cls, hashing_method) -> list["ImageHash"]:
        db = Db(f"hashes_{hashing_method}")
        db_data: dict[str, list[dict[str, str]]] = db.data
        del db

        hashes: list["ImageHash"] = []
        for user, data in db_data.items():
            for item in data:
                hash = item.get("hash")
                name = item.get("name")
                method = item.get("method")

                if hash is None or name is None or method is None:
                    logging.warning(f"Could not import a hash for user {user}")
                    continue

                hashes.append(cls(hash, method, img_name=name))

        if not hashes:
            print(
                "[red]Warning[/red]: No hashes found in db. They should be generated for matching"
            )

        return hashes


class HashJobBuilder:
    def __init__(self) -> None:
        self.img_path: Optional[Path] = None
        self.img: Optional[Image.Image] = None
        self.hash_len: int = 16
        self.method: type[HashMethod] = AverageHash

    def set_img_path(self, img_path: Path) -> "HashJobBuilder":
        self.img_path = img_path
        return self

    def set_img(self, img: Image.Image) -> "HashJobBuilder":
        self.img = img
        return self

    def set_hash_len(self, hash_len: int) -> "HashJobBuilder":
        self.hash_len = hash_len
        return self

    def set_method(self, method: type[HashMethod]):
        self.method = method
        return self

    def build(self):
        if self.img_path == self.img:
            raise ValueError("img_path or img need to be set for HashJobBuilder")

        if self.img_path is not None:
            if self.img is not None:
                logging.warning(
                    "Both img_path and img is given to HashJobBuilder, using the img_path by default"
                )
                self.img = Image.open(self.img_path)

        obj = self.method(img=self.img, hash_len=self.hash_len)
        return obj.hash()

    def build_hash_obj(self):
        """Builds the ImageHash object. Use build() method to return hash only"""

        if self.img is None:
            raise ValueError("no img given to build_hash_obj")

        if self.method is None:
            raise ValueError("no hashing method given to build_hash_obj")

        if self.img_path is None:
            raise ValueError("no img_path given to build_hash_obj")

        obj = self.method(img=self.img, hash_len=self.hash_len)

        return ImageHash(obj.hash(), obj.name, img_path=self.img_path)
