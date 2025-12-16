from fastapi import APIRouter
from pydantic import BaseModel
from src import db
from src import config as cf
from . import lib
from pathlib import Path

router = APIRouter()
CONFIG:cf.Config = cf.Config.from_env()

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

@router.get("/modify/health")
def health():
    return {"status": "ok"}
