from fastapi import APIRouter
from pydantic import BaseModel
from . import lib
from .lib import CONFIG, logger
import time
import psycopg2
from .db import ModifiedImage
from pathlib import Path

router = APIRouter()

class ModImageInput(BaseModel):
    id:int
    path:str
    image_id:int
    modification_id:int
    def into_db_modimage(self):
        return ModifiedImage(self.id, Path(self.path), self.image_id, self.modification_id)

class HashRequest(BaseModel):
    modified_image: ModImageInput
    limit: int

class HashResponse(BaseModel):
    id:int
    hash:str
    mod_img_id:int
    hash_method_id:int
    

@router.post("/hash/next")
def hash_image(req:HashRequest):
    wait_for_db(CONFIG.postgresql_host, CONFIG.postgresql_port, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_db)
    hashes = []

    loader = lib.Hasher(req.limit)

    for hash in loader.start_iter(req.modified_image.into_db_modimage()):
        hashes.append(
            HashResponse(
                id=hash.id,
                hash=hash.hash,
                mod_img_id=hash.modified_image_id,
                hash_method_id=hash.hashing_method_id
            )
        )

        if len(hashes) >= req.limit:
            break

    return {"hashes": hashes}

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

@router.get("/hash/health")
def health():
    return {"status": "ok"}
