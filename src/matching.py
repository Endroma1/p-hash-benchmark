import logging
from typing import Optional
from hashing_methods import ImageHash
from db import Db


class MatchResult:
    def __init__(
        self,
        input_img: str,
        db_img: str,
        hamming_distance: Optional[int] = None,
        is_same_user: Optional[bool] = None,
        is_same_image: Optional[bool] = None,
    ) -> None:
        self._input_img = input_img
        self._db_img = db_img
        self._hamming_distance = hamming_distance
        self._is_same_user = is_same_user
        self._is_same_image = is_same_image

    def set_hamming_distance(self, hamming_distance: int):
        self._hamming_distance = hamming_distance
        return self

    def set_is_same_user(self, same_user: bool):
        self._is_same_user = same_user
        return self

    def set_is_same_image(self, same_image: bool):
        self._is_same_image = same_image
        return self

    def save_to_db(self, db: Optional[Db] = None, db_name: Optional[str] = None):
        if db is None and db_name is not None:
            db = Db(db_name)
        elif db is None and db_name is None:
            raise ValueError("No db or db_name given to save_to_db")

        assert db is not None

        entry = [
            {
                "input_img": self._input_img,
                "db_img": self._db_img,
                "hamming_distance": self._hamming_distance,
                "is_same_user": self._is_same_user,
                "is_same_image": self._is_same_image,
            }
        ]

        db.add(entry, "Matches")
        db.save()


class MatchingProcess:
    def __init__(self, image_hash: ImageHash) -> None:
        self.image_hash = image_hash
        self.db_hashes = ImageHash.load_all_hashes_from_db(image_hash.method)
        self.match_results: list["MatchResult"] = []
        self.start()

    def start(self):
        for img_hash in self.db_hashes:

            result = MatchResult(self.image_hash.name, img_hash.name)

            if self.image_hash.user() == img_hash.user():
                result.set_is_same_user(True)
            else:
                result.set_is_same_user(False)

            if self.image_hash.name == img_hash.name:
                result.set_is_same_image(True)
            else:
                result.set_is_same_image(False)

            try:
                h_dist = self._hamming_distance(self.image_hash.as_bin, img_hash.as_bin)
            except Exception as e:
                logging.error(
                    f"Could not calculate hamming distance between {self.image_hash.name} and {img_hash.name}, {e}"
                )
                continue

            result.set_hamming_distance(h_dist)

            self.match_results.append(result)

    def _hamming_distance(self, b_str1: str, b_str2: str):
        if len(b_str1) != len(b_str2):
            raise ValueError(
                "_hamming_distances did not get two equal length bitstrings"
            )

        diff = int(b_str1, 2) ^ int(b_str2, 2)
        diff_b = format(diff, "04b")
        h_dist = diff_b.count("1")

        return h_dist

    def save_results(self):
        db = Db(f"matches-{self.image_hash.method}")
        for result in self.match_results:
            result.save_to_db(db)
