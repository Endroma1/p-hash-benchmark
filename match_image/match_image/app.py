from fastapi import FastAPI
from pydantic import BaseModel
from match_image import lib

app = FastAPI(title="Hash Matcher")

class LoadRequest(BaseModel):
    limit: int = 10

class MatchResponse(BaseModel):
    id: int
    hamming_distance: float
    hash_id1: int
    hash_id2: int


@app.post("/match")
def match_hashes(req:LoadRequest):
    matches = []

    loader = lib.Matcher

    for match in loader.start_iter():
        matches.append(
            MatchResponse(
                id=match.id,
                hamming_distance=match.hamming_distance,
                hash_id1=match.hash_id1,
                hash_id2=match.hash_id2
            )
        )

        if len(matches) >= req.limit:
            break

    return {"matches": matches}

