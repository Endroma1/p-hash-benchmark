from typing import Generator
from . import config as cf
from dataclasses import dataclass
from pathlib import Path
from . import db
import psycopg2

CONFIG:cf.Config = cf.Config.from_env()

@dataclass
class Image:
    id: int
    path: Path
    user_id: int

class ImageLoader():
    @staticmethod
    def start_iter():
        """
        Lazily loads all images from input dir and sends to db. Used by other programs to get back Image instead of having to ask db
        """
        with db.Database(CONFIG.postgresql_db, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_host, CONFIG.postgresql_port) as pg:
            for file, user in read_images_iter(CONFIG):
                user_id = pg.add_user(user)
                if user_id is None:
                    user_id = pg.get_user_id(user)
                img_id = pg.add_image(file, user_id)

                yield Image(img_id, file, user_id)


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

