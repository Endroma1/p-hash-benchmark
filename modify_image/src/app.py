from dataclasses import dataclass
import time
from pathlib import Path

import psycopg2
from PIL import Image
from typing import Generator
import config as cf
import image
import modification
import hashlib
import db

CONFIG:cf.Config = cf.Config.from_env()

@dataclass
class DatabaseImage:
    id: int
    path: Path
    user_id: int

def main():
    CONFIG.modified_img_path.mkdir(exist_ok=True, parents=True)


    with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as pg:
        for file, user in read_images_iter(CONFIG):
            user_id = pg.add_user(user)
            if user_id is None:
                user_id = pg.get_user_id(user)
            id = pg.add_image(file, user_id)


            img = DatabaseImage(id, file, user_id)

            
            process_image(img, CONFIG.modified_img_path, pg)

def read_images_iter(config:cf.Config)->Generator[tuple[Path, str]]:
    """
    Reads images from config dir
    """
    base_dir = config.input_img_path

    if not base_dir.exists():
        raise ValueError(f"Input path {base_dir} does not exist")

    for file in base_dir.rglob("*"):
        if file.is_file():
            try:
                rel_parent = file.parent.relative_to(base_dir)
                stem = file.parent.stem if rel_parent.parts else None
            except ValueError:
                stem = None

            if stem:
                yield (file, stem)
            else:
                yield (file, "undefined")
            

def process_image(img_obj:Image, save_path:Path, database:db.Database):
    """
    Processes each image, opens it, modifies it, and saves it to a hashed path. Returns modified image path
    """
    for mod_name, Mod in modification.Modifications().modifications.items():
        img:Image.Image = image.open_image(img_obj.path)

        mod_img:Image.Image = Mod().modify_image(img)

        hash = hash_image(mod_img)

        save_filepath = (save_path / hash).with_suffix('.png')

        image.save_image(save_filepath, mod_img)

        with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as pg:
            try:
                database.add_mod_image(save_filepath, img_obj.path.name,img_obj.id, mod_name)
            except db.ModificationIDNotFound:
                database.add_modification(mod_name).commit()
                database.add_mod_image(save_filepath, img_obj.path.name,img_obj.id, mod_name)

def hash_image(img:Image.Image)->str:
    hasher = hashlib.blake2b(usedforsecurity=False)
    hasher.update(img.tobytes())
    hasher.update(img.mode.encode())
    hash = hasher.hexdigest()

    return hash 

if __name__ == "__main__":
    while True:
        try:
            main()
        except psycopg2.OperationalError:
            time.sleep(1)
            continue

        break
