from typing import Generator
from . import config as cf
from dataclasses import dataclass
from pathlib import Path
from . import db
import psycopg2
import logging
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
CONFIG:cf.Config = cf.Config.from_env()

@dataclass
class Image:
    id: int
    path: Path
    user_id: int

class ImageLoader():
    """
    Lazily loads all images from input dir and sends to db. Used by other programs to get back Image instead of having to ask db.
    Use start_iter
    """
    def __init__(self, batch_size: int) -> None:
        self.batch_size: int = batch_size # How many images should be processed before being sent to db
        self.pending = 0
        self.database = db.Database(CONFIG.postgresql_db, 
                                    CONFIG.postgresql_user, 
                                    CONFIG.postgresql_passwd, 
                                    CONFIG.postgresql_host, 
                                    CONFIG.postgresql_port)
    def start_iter(self)->Generator[Image]:
        """
        Ensures that images are commited to db when there are no more images, even if batch_size is not hit
        """
        try:
            for img in self._process_images_iter():
                yield img
        finally:
            if self.pending > 0:
                self.database.commit()
            self.database.close()

    def _process_images_iter(self)->Generator[Image]:
        """
        Processes each image by sending to db and creating image object to return
        """
        for file, user in read_images_iter(CONFIG):
            logger.info(f"Processing image: {file}, user: {user}")
            user_id = self.database.add_user(user) or self.database.get_user_id(user)
            img_id = self.database.add_image(file, user_id)

            self.pending += 1

            if self.pending >= self.batch_size:
                self.database.commit()
                self.pending = 0

            logger.info(f"Added img {img_id} to db")
            yield Image(img_id, file, user_id)

def read_images_iter(config:cf.Config)->Generator[tuple[Path, str]]:
    """
    Reads images from config dir returning (path, user)
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

