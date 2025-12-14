from fastapi import FastAPI
from pydantic import BaseModel
from load_image import lib

app = FastAPI(title="Image loader service")



class LoadRequest(BaseModel):
    limit: int = 10

class ImageResponse(BaseModel):
    id: int
    path: str
    user_id: int

@app.post("/load/next")
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

@app.get("/health")
def health():
    return {"status": "ok"}

