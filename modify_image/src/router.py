from fastapi import APIRouter
from pydantic import BaseModel
import psycopg2
from src import db
from src import config as cf
from . import lib
from .lib import CONFIG, logger
from pathlib import Path
import time

router = APIRouter()

class ImageInput(BaseModel):
    id: int
    path: str
    user_id: int

    def into_db_image(self):
        return db.Image(self.id, Path(self.path), self.user_id)

class ModifyRequest(BaseModel):
    image: ImageInput
    limit: int

class ModifiedImageResponse(BaseModel):
    id: int
    path: str
    image_id:int
    modification_id:int

@router.post("/modify/next")
def modify_image(req: ModifyRequest):
    wait_for_db(CONFIG.postgresql_host, CONFIG.postgresql_port, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_db)
    images = []

    loader = lib.ImageModifier(req.limit)

    for img in loader.start_iter(req.image.into_db_image()):
        images.append(
            ModifiedImageResponse(
                id=img.id,
                path=str(img.path),
                image_id=img.image_id,
                modification_id=img.modification_id
            )
        )

        if len(images) >= req.limit:
            break

    return {"modified_images": images}

def wait_for_db(host, port, user, password, dbname, retries=10, delay=5):
    """
    Polls PostgreSQL until it accepts connections.
    """
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
                connect_timeout=2  # short timeout per attempt
            )
            conn.close()
            logger.info("PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            logger.warning("DB not ready yet (attempt %d/%d): %s", attempt, retries, e)
            time.sleep(delay)
    raise RuntimeError(f"Database {host}:{port} not ready after {retries} attempts")

@router.get("/modify/health")
def health():
    return {"status": "ok"}
