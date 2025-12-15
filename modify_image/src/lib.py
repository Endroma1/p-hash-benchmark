from dataclasses import dataclass
from pathlib import Path
from PIL import Image
from src import image
from src import modification 
from src import db
from src import config as cf
import hashlib
from typing import Generator

@dataclass
class ModifiedImage:
    id:int
    path:Path
    image_id:int
    modification_id:int

CONFIG:cf.Config = cf.Config.from_env()



class ImageModifier():
    @staticmethod
    def start_iter(img_obj:db.Image)->Generator[ModifiedImage]:
        """
        Processes each image, opens it, modifies it, and saves it to a hashed path. Returns modified image path
        """
        save_path = CONFIG.modified_img_path
        with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as database:
            for mod_name, Mod in modification.Modifications().modifications.items(): 
                img:Image.Image = image.open_image(img_obj.path)

                mod_img:Image.Image = Mod().modify_image(img)

                hash = hash_image(mod_img)

                save_filepath = (save_path / hash).with_suffix('.png')

                image.save_image(save_filepath, mod_img)
                try:
                    mod_id:int = database.get_mod_id(mod_name)
                except db.ModificationIDNotFound:
                    mod_id = database.add_modification(mod_name)


                id = database.add_mod_image(save_filepath, img_obj.id, mod_id)

                yield ModifiedImage(id, save_filepath, img_obj.id, mod_id)

def hash_image(img:Image.Image)->str:
    hasher = hashlib.blake2b(usedforsecurity=False)
    hasher.update(img.tobytes())
    hasher.update(img.mode.encode())
    hash = hasher.hexdigest()

    return hash 

