from dataclasses import dataclass
from pathlib import Path
from PIL import Image
from src import image
from src import modification 
from src import db
from src import config as cf
import hashlib
from typing import Generator
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

@dataclass
class ModifiedImage:
    id:int
    path:Path
    image_id:int
    modification_id:int

CONFIG:cf.Config = cf.Config.from_env()



class ImageModifier():
    def __init__(self, batch_size: int) -> None:
        self.batch_size: int = batch_size # How many images should be processed before being sent to db
        self.pending = 0
        self.database = db.Database(CONFIG.postgresql_db, 
                                    CONFIG.postgresql_user, 
                                    CONFIG.postgresql_passwd, 
                                    CONFIG.postgresql_host, 
                                    CONFIG.postgresql_port)

    def start_iter(self, img_obj:db.Image)->Generator[Image]:
        """
        Ensures that modifications are commited to db when there are no more images, even if batch_size is not hit
        """
        try:
            for mod_img in self._process_iter(img_obj):
                yield mod_img
        finally:
            if self.pending > 0:
                self.database.commit()
            self.database.close()

    def _process_iter(self,img_obj:db.Image)->Generator[ModifiedImage]:
        """
        Processes each image, opens it, modifies it, and saves it to a hashed path. Returns modified image path
        """
        save_path = CONFIG.modified_img_path
        for mod_name, Mod in modification.Modifications().modifications.items(): 

            logger.info(f"Processing modification: {mod_name}, img: {img_obj.path.name}")
            img:Image.Image = image.open_image(img_obj.path)

            mod_img:Image.Image = Mod().modify_image(img)

            hash = hash_image(mod_img)

            save_filepath = (save_path / hash).with_suffix('.png')

            image.save_image(save_filepath, mod_img)
            mod_id:int = self.database.get_mod_id(mod_name) or self.database.add_modification(mod_name)

            self.pending += 1

            if self.pending >= self.batch_size:
                self.database.commit()
                self.pending = 0

            id = self.database.add_mod_image(save_filepath, img_obj.id, mod_id)

            yield ModifiedImage(id, save_filepath, img_obj.id, mod_id)

def hash_image(img:Image.Image)->str:
    hasher = hashlib.blake2b(usedforsecurity=False)
    hasher.update(img.tobytes())
    hasher.update(img.mode.encode())
    hash = hasher.hexdigest()

    return hash 

