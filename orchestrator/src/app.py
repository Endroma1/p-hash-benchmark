from dataclasses import dataclass
from typing import AsyncGenerator 
from . import config
import asyncio
import httpx
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG = config.Config.from_env()

@dataclass
class HealthCheckError(Exception):
    component_name:str
    def __str__(self) -> str:
        return f"Failed healthcheck for {self.component_name}"

class ComponentResponse(BaseModel):
    pass

class LoadResponse(ComponentResponse):
    id: int
    path: str
    user_id: int

class ModifiedImageResponse(ComponentResponse):
    id: int
    path: str
    image_id:int
    modification_id:int

class HashResponse(ComponentResponse):
    id:int
    hash:str
    mod_img_id:int
    hash_method_id:int

class MatchStatusResponse(ComponentResponse):
    status:str


@dataclass
class Component:
    """
    Represents a p-hash component. Attempts to get the data from the component if health check succeeds.
    """
    url:str
    health_path:str
    response_type: type[ComponentResponse]
    response_key: str
    _client:httpx.AsyncClient|None = None

    async def start_iter(self, path:str, json:dict|None = None)->AsyncGenerator[ComponentResponse]:
        """
        Checks health of the component. If it succeeds it starts yielding the responses from the component given by `response_type`
        """
        if self._client is None:
            self._client = httpx.AsyncClient()

        await self.check_health()

        while True:
            resp = await self._client.post(f"{self.url}{path}", json=json)
            result:dict = resp.json()

            loaded: list[ComponentResponse] = [self.response_type(**item) for item in result[self.response_key]]
            if not loaded:
                logging.info(f"No more {self.response_type.__name__} received from endpoint.")
                await asyncio.sleep(10)
                continue

            for load in loaded:
                yield load

            await asyncio.sleep(0)

    async def check_health(self, retries = 10):
        """
        Health checks the client
        """
        if self._client is None:
            self._client = httpx.AsyncClient()

        health_retries = 1
        while True:
            resp = await self._client.get(f"{self.url}{self.health_path}")
            result = resp.json()
            try:
                if result["status"] == "ok":
                    break
            except Exception as e:
                if health_retries > retries:
                    raise HealthCheckError(self.response_type.__name__)
                logger.warning(f"Endpoint not found {e}, attempt {health_retries}/{retries} . Retrying...")
                health_retries += 1
            await asyncio.sleep(5)

    async def wait_until_done(
        self,
        path: str,
        status_key: str = "state",
        done_value: str = "done",
        interval: int = 5,
    ):
        if self._client is None:
            self._client = httpx.AsyncClient()

        while True:
            resp = await self._client.get(f"{self.url}{path}")
            result = resp.json()

            state = result.get(status_key)
            logger.info(f"{self.url} status: {state}")

            if state == done_value:
                return

            if state == "failed":
                raise RuntimeError(f"{self.url} failed")

            await asyncio.sleep(interval)

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        assert self._client is not None
        await self._client.aclose()

#################
### FUNCTIONS ###
#################

async def main():
    await run_pipeline()
    await wait_for_hashing()
    logging.info("Pipeline done")
    await run_match()

async def run_pipeline():
    loader = Component(CONFIG.loader_url, "/load/health", response_type=LoadResponse, response_key="images")
    modifier = Component(CONFIG.modifier_url, "/modify/health", response_type=ModifiedImageResponse,response_key="modified_images")
    hasher = Component(CONFIG.hasher_url, "/hash/health", response_type=HashResponse, response_key="hashes")

    logging.info("Starting loading")
    async for load_result in loader.start_iter(path="/load/next",json={"limit":10}):

        logging.info("Starting modification")
        async for mod_result in modifier.start_iter(path="/modify/next",json={"image": load_result.model_dump(),"limit": 10}):

            logging.info("Starting hashing")
            async for hash_result in hasher.start_iter(path="/hash/next",json={"image": mod_result.model_dump(),"limit": 10}):
                pass


async def wait_for_hashing():
    hasher_status = Component(
        CONFIG.hasher_url,
        health_path="/hash/health",
        response_type=MatchStatusResponse,
        response_key="status",
    )

    await hasher_status.wait_until_done("/hash/status")

async def run_match():
    logging.info("Starting matching")
    matcher = Component(CONFIG.matcher_url, "/match/health",response_type=ModifiedImageResponse, response_key="state")

    # Match happens only when hashing is done with all images and don't pass hash result as it reads from db.
    async for match_state in matcher.start_iter("/match/start"):
        logging.info(f"Match state: {match_state}")

if __name__ == "__main__":
    asyncio.run(main())
