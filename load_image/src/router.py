from fastapi import APIRouter
from pydantic import BaseModel
from . import lib

router = APIRouter()

class LoadRequest(BaseModel):
    limit: int = 10

class ImageResponse(BaseModel):
    id: int
    path: str
    user_id: int

@router.post("/load/next")
def load_next(req: LoadRequest):
    images = []

    loader = lib.ImageLoader

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

    return {"images": images}

@router.get("/load/health")
def health():
    return {"status": "ok"}

