from dataclasses import dataclass
from typing import Generator
import psycopg2
from hash_image import config as cf
from hash_image import db
from hash_image import hash_image
import time
from PIL import Image

CONFIG = cf.Config.from_env()

@dataclass
class Hash:
    id: int
    hash: str
    modified_image_id:int
    hashing_method_id:int

def main():
    pass

class Hasher:
    @staticmethod
    def start_iter(img: db.ModifiedImage )->Generator[Hash]:
        """
        Hashes one image and returns all hashes from hashing method(s)
        """
        with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as database:
            for name, Method in hash_image.HashingMethods().hashing_methods.items():

                with Image.open(img.image_path) as open_image:
                    loaded_img = open_image.convert("RGB").copy()

                hash = Method().hash_image(loaded_img)
                try:
                    hash_method_id = database.get_hash_method_id(name)
                except db.HashMethodIDNotFound:
                    hash_method_id = database.add_hash_method(name)

                id = database.send_hash(hash, img.id, hash_method_id)

                yield Hash(id, hash, img.id, hash_method_id)

def open_image(img: db.ModifiedImage):
    Image.open(img.image_path)


if __name__ == "__main__":
    while True:
        try:
            main()
        except psycopg2.OperationalError:
            time.sleep(1)
            continue

        break
