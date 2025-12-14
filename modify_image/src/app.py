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


def main():
    CONFIG.modified_img_path.mkdir(exist_ok=True, parents=True)

    with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as pg:
        start = 1
        fetch_amount = 100
        last_id = 0

        while True:
            found_images = False

            generator:Generator[db.Image] = pg.get_images(start, fetch_amount)

            for image in generator:
                found_images = True
                process_image(image, CONFIG.modified_img_path, pg)
                last_id = image.id

            if not found_images:
                #time.sleep(5)   Use if always running, else it exists when no more images are found
                break

            start = last_id + 1

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
