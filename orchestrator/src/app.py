from . import config
import asyncio
import httpx
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG = config.Config.from_env()

class LoadResponse(BaseModel):
    id: int
    path: str
    user_id: int

class ModifiedImageResponse(BaseModel):
    id: int
    path: str
    image_id:int
    modification_id:int

class HashResponse(BaseModel):
    id:int
    hash:str
    mod_img_id:int
    hash_method_id:int


async def main():
    async with httpx.AsyncClient() as client:
        while True:
            resp= await client.get(f"{CONFIG.loader_url}/load/health")
            result = resp.json()
            try:
                if result["status"] == "ok":
                    break
            except KeyError as e:
                logger.warning(f"Endpoint not found {e}")
            await asyncio.sleep(5)

        resp = await client.post(f"{CONFIG.loader_url}/load/next", json={"limit": 10})
        result:dict = resp.json()

        loaded: list[LoadResponse] = [LoadResponse(**item) for item in result["images"]]


        logger.info("Starting modification")
        for load in loaded:
            while True:
                resp= await client.get(f"{CONFIG.modifier_url}/load/health")
                result = resp.json()
                    
                try:
                    if result["status"] == "ok":
                        break
                except KeyError as e:
                    logger.warning(f"Endpoint not found {e}")
            await asyncio.sleep(5)
            resp = await client.post(f"{CONFIG.modifier_url}/modify/next", json={"image": load.model_dump(),"limit": 10})
            result = resp.json()

            mods: list[ModifiedImageResponse] = [ModifiedImageResponse(**item) for item in result["modified_images"]]


            logger.info("Starting hashing")
            for mod in mods:
                while True:
                    resp= await client.get(f"{CONFIG.hasher_url}/load/health")
                    result = resp.json()
                    try:
                        if result["status"] == "ok":
                            break
                    except KeyError as e:
                        logger.warning(f"Endpoint not found {e}")
                    await asyncio.sleep(5)
                resp = await client.post(f"{CONFIG.hasher_url}/hash/next", json={"modified_image": mod.model_dump(), "limit":10})
                result = resp.json()



        logger.info("Starting matching")
        while True:
            resp= await client.get(f"{CONFIG.matcher_url}/load/health")
            result = resp.json()
            try:
                if result["status"] == "ok":
                    break
            except KeyError as e:
                logger.warning(f"Endpoint not found {e}")
            await asyncio.sleep(5)
        resp = await client.post(f"{CONFIG.matcher_url}/match/start")
    
if __name__ == "__main__":
    asyncio.run(main())
