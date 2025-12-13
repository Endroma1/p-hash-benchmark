from pathlib import Path
import config as cf
import image
import modification
import hashlib
import db
from PIL import Image

CONFIG:cf.Config = cf.Config.from_env()

def main():
    if not CONFIG.input_img_path.is_dir():
        raise ValueError("Input img path was not a directory")

    CONFIG.modified_img_path.mkdir(exist_ok=True, parents=True)

    img_paths = [p for p in CONFIG.input_img_path.rglob("*") if p.is_file()]

    for path in img_paths:
        process_image(path, CONFIG.modified_img_path)

def process_image(img_path:Path, save_path:Path):
    """
    Processes each image, opens it, modifies it, and saves it to a hashed path. Returns modified image path
    """
    for mod_name, Mod in modification.Modifications().modifications.items():
        img:Image.Image = image.open_image(img_path)

        mod_img:Image.Image = Mod().modify_image(img)

        hash = hash_image(mod_img)

        save_filepath = (save_path / hash).with_suffix('.png')

        image.save_image(save_filepath, mod_img)

        with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as pg:
            try:
                pg.add_image(save_filepath, img_path.name, mod_name)
            except db.ModificationIDNotFound:
                pg.add_modification(mod_name)
                pg.add_image(save_filepath, img_path.name, mod_name)

def hash_image(img:Image.Image)->str:
    hasher = hashlib.blake2b(usedforsecurity=False)
    hasher.update(img.tobytes())
    hasher.update(img.mode.encode())
    hash = hasher.hexdigest()

    return hash 

if __name__ == "__main__":
    main()
