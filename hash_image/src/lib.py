from dataclasses import dataclass
from typing import Generator
import psycopg2
from src import config as cf
from src import db
from src import hash_image
import time
from PIL import Image
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

CONFIG = cf.Config.from_env()

@dataclass
class Hash:
    id: int
    hash: str
    modified_image_id:int
    hashing_method_id:int


class Hasher:
    def __init__(self, batch_size: int) -> None:
        self.batch_size: int = batch_size # How many images should be processed before being sent to db
        self.pending = 0
        self.database = db.Database(CONFIG.postgresql_db, 
                                    CONFIG.postgresql_user, 
                                    CONFIG.postgresql_passwd, 
                                    CONFIG.postgresql_host, 
                                    CONFIG.postgresql_port)
    def start_iter(self, img_obj:db.ModifiedImage)->Generator[Image]:
        """
        Ensures that modifications are commited to db when there are no more images, even if batch_size is not hit
        """
        try:
            for hash in self._process_iter(img_obj):
                yield hash
        finally:
            if self.pending > 0:
                self.database.commit()
            self.database.close()

    def _process_iter(self,img: db.ModifiedImage )->Generator[Hash]:
        """
        Hashes one image and returns all hashes from hashing method(s)
        """
        for name, Method in hash_image.HashingMethods().hashing_methods.items():
            logger.info(f"Processing hashing_method: {name}, img: {img.image_path.name}")

            with Image.open(img.image_path) as open_image:
                loaded_img = open_image.convert("RGB").copy()

            hash = Method().hash_image(loaded_img)
            hash_method_id = self.database.add_hash_method(name) or self.database.get_hash_method_id(name)

            self.pending += 1

            if self.pending >= self.batch_size:
                self.database.commit()
                self.pending = 0
            id = self.database.send_hash(hash, img.id, hash_method_id) 
            if id is None:
                logging.info(f"Hash {hash} from image {img.id} with method {hash_method_id} already found in db")
                continue

            yield Hash(id, hash, img.id, hash_method_id)

def open_image(img: db.ModifiedImage):
    Image.open(img.image_path)


