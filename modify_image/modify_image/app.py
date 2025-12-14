from fastapi import FastAPI
from pydantic import BaseModel
from modify_image import db
from modify_image import config as cf
from modify_image import lib
from pathlib import Path

app = FastAPI(title="Image Modification Service")
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

@app.post("/modify")
def modify_image(req: ModifyRequest):
    images = []

    loader = lib.ImageModifier

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
