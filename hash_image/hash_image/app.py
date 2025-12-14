from fastapi import FastAPI
from pydantic import BaseModel
from hash_image import lib

app=FastAPI(title="Image hasher")

class ModImageInput(BaseModel):
    id:int
    path:str
    image_id:int
    modification_id:int

class HashRequest(BaseModel):
    modified_image: ModImageInput
    limit: int

class HashResponse(BaseModel):
    id:int
    hash:str
    mod_img_id:int
    hash_method_id:int
    

@app.post("/hash")
def hash_image(req):
    hashes = []

    loader = lib.Hasher

    for hash in loader.start_iter(req.image.into_db_image()):
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

    return {"modified_images": hashes}

