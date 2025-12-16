from fastapi import APIRouter
from pydantic import BaseModel
import time
import psycopg2
from . import lib
from .lib import CONFIG, logger
router = APIRouter()

class LoadRequest(BaseModel):
    limit: int = 10

class ImageResponse(BaseModel):
    id: int
    path: str
    user_id: int

@router.post("/load/next")
def load_next(req: LoadRequest):
    wait_for_db(CONFIG.postgresql_host, CONFIG.postgresql_port, CONFIG.postgresql_user, CONFIG.postgresql_passwd, CONFIG.postgresql_db)
    images = []

    loader = lib.ImageLoader(req.limit)
    try:
        for img in loader.start_iter():
            images.append(
                ImageResponse(
                    id=img.id,
                    path=str(img.path),
                    user_id=img.user_id
                )
            )

            if len(images) >= req.limit:
                break
    except Exception as e:
        logger.warning(f"Failed to get image: {e}")

    return {"images": images}

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

@router.get("/load/health")
def health():
    return {"status": "ok"}

